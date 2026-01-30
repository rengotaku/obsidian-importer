"""
Commands - CLIメインコマンド

main() エントリーポイントの実装。
status/metrics コマンドは別モジュールに分離。
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import INDEX_DIR, DUST_DIR
from normalizer.state.manager import load_state, delete_state
from normalizer.io.files import list_index_files, cleanup_empty_folders
from normalizer.io.session import start_new_log_session, log_message
from normalizer.pipeline.prompts import set_stage_debug_mode
from normalizer.output.diff import process_file_with_diff
from normalizer.processing.single import process_single_file
from normalizer.processing.batch import process_all_files
from normalizer.cli.parser import create_parser
from normalizer.cli.status import cmd_status
from normalizer.cli.metrics import cmd_metrics


def main() -> int:
    """メインエントリーポイント"""
    parser = create_parser()
    args = parser.parse_args()

    # --stage-debug モード設定
    if hasattr(args, 'stage_debug') and args.stage_debug:
        set_stage_debug_mode(True)

    # --status モード
    if args.status:
        return cmd_status(output_json=args.json, verbose=args.verbose)

    # --metrics モード
    if args.metrics:
        return cmd_metrics(output_json=args.json)

    # --reset オプション
    if args.reset:
        delete_state()
        if not args.quiet:
            print("🔄 処理状態をリセットしました")

    # 引数なしの場合は --all と同じ動作
    if not args.file and not args.all and not args.preview and not args.status and not args.metrics:
        args.all = True

    # @dust フォルダチェック
    if args.all or args.preview:
        dust_files = list(DUST_DIR.glob("*.md")) if DUST_DIR.exists() else []
        if dust_files:
            _print_dust_warning(dust_files)
            return 1

    # 単一ファイル処理
    if args.file:
        return _process_single(args)

    # 全ファイル処理
    if args.all or args.preview:
        return _process_all(args)

    return 0


def _print_dust_warning(dust_files: list) -> None:
    """@dust フォルダ警告を表示"""
    print(f"⚠️ @dust フォルダに {len(dust_files)} ファイルが存在します")
    print("   処理前に @dust を確認・削除してください:")
    for f in dust_files[:5]:
        print(f"     - {f.name}")
    if len(dust_files) > 5:
        print(f"     ... 他 {len(dust_files) - 5} ファイル")
    print("\n   削除コマンド: rm -rf @dust/*.md")


def _process_single(args) -> int:
    """単一ファイル処理"""
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"❌ ファイルが見つかりません: {filepath}")
        return 1

    # diffモード
    if args.diff:
        return process_file_with_diff(filepath)

    if not args.quiet:
        print(f"📄 処理対象: {filepath}")
        print("⏳ Ollama API呼び出し中...")

    result = process_single_file(
        filepath,
        preview=False,
        quiet=args.quiet,
        output_json=args.json
    )

    return 0 if result["success"] else 1


def _process_all(args) -> int:
    """全ファイル処理"""
    files = list_index_files()
    if not files:
        print("📂 処理対象ファイルがありません")
        return 0

    # 直下/サブフォルダ別カウント
    direct_files = [f for f in files if f.parent == INDEX_DIR]
    subfolder_files = [f for f in files if f.parent != INDEX_DIR]

    if not args.quiet:
        print(f"📂 処理対象: {len(files)} ファイル")
        print(f"   ├─ 直下: {len(direct_files)} ファイル")
        print(f"   └─ サブフォルダ: {len(subfolder_files)} ファイル")
        if args.preview:
            print("👁️ プレビューモード（移動なし）")

    # 大量ファイル処理時の確認
    if not _confirm_large_batch(args, files, subfolder_files):
        return 1

    # セッション管理
    state = _handle_session(args)
    if state is False:
        return 1

    # バッチ処理実行
    summary = process_all_files(
        files,
        preview=args.preview,
        quiet=args.quiet,
        output_json=args.json,
        state=state
    )

    # 結果ログ
    stats = summary["stats"]
    log_message(
        f"処理完了: 成功={stats['success']}, dust={stats['dust']}, "
        f"review={stats['review']}, エラー={stats['error']}",
        also_print=False
    )

    # 空フォルダクリーンアップ
    if not args.no_cleanup_empty and not args.preview:
        _cleanup_empty(args)

    # エラーがあった場合は終了コード1
    if summary["stats"]["error"] > 0:
        return 1

    return 0


def _confirm_large_batch(args, files: list, subfolder_files: list) -> bool:
    """大量ファイル処理時の確認プロンプト"""
    CONFIRM_THRESHOLD = 20
    if len(files) < CONFIRM_THRESHOLD or args.force or args.quiet:
        return True

    print(f"\n⚠️ {len(files)} ファイルを処理します")
    print("\n📋 処理対象ファイル（先頭20件）:")
    for i, f in enumerate(files[:20]):
        rel_path = f.relative_to(INDEX_DIR)
        depth = len(rel_path.parts) - 1
        indent = "  " * depth
        print(f"   {i+1:3}. {indent}{f.name}")
    if len(files) > 20:
        print(f"   ... 他 {len(files) - 20} ファイル")

    # サブフォルダの分布を表示
    if subfolder_files:
        folders = {}
        for f in subfolder_files:
            folder = f.parent.name
            folders[folder] = folders.get(folder, 0) + 1
        print(f"\n📁 サブフォルダ分布:")
        for folder, count in sorted(folders.items(), key=lambda x: -x[1])[:10]:
            print(f"   {folder}: {count} ファイル")
        if len(folders) > 10:
            print(f"   ... 他 {len(folders) - 10} フォルダ")

    print(f"\n続行しますか？ [y/N]: ", end="")
    try:
        response = input().strip().lower()
        if response not in ("y", "yes"):
            print("❌ 処理を中止しました")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 処理を中止しました")
        return False

    return True


def _handle_session(args) -> dict | None | bool:
    """セッション管理。False を返すと処理中止"""
    state = load_state()

    # pending のうち、@index に実際に存在するファイルのみを有効とみなす
    if state and state.get("pending"):
        actual_pending = [f for f in state["pending"] if (INDEX_DIR / f).exists()]
        if len(actual_pending) != len(state["pending"]):
            # 存在しないファイルがあった場合、pending を更新
            state["pending"] = actual_pending
            # pending が全て消えた場合は state を無効化して新規セッション開始
            if not actual_pending:
                state = None

    # pending が空（前回正常終了）なら自動的に新規セッション開始
    if state and not state.get("pending"):
        state = None

    if state and state.get("pending"):
        if args.new:
            print(f"📁 前回のセッションを保持して新規開始")
            state = None
        elif args.resume:
            print(f"🔄 中断セッションを続行: 残り {len(state['pending'])} ファイル")
        else:
            print(f"\n⚠️ 中断セッションがあります")
            print(f"   セッションID: {state.get('session_id', 'unknown')}")
            print(f"   処理済み: {len(state['processed'])} / 残り: {len(state['pending'])}")
            print(f"\n💡 オプション:")
            print(f"   --resume  : 中断セッションを続行")
            print(f"   --new     : 新規セッション開始（履歴は残る）")
            print(f"   --reset   : セッションを削除して新規開始")
            return False
    elif args.new:
        # pending が空でも --new なら新規セッション開始
        state = None

    if state is None:
        # 新規セッション開始（StateManagerにも自動設定される）
        start_new_log_session()
        files = list_index_files()
        log_message(f"処理開始: {len(files)} ファイル (preview={args.preview})", also_print=False)
    else:
        log_message(f"処理再開: 残り {len(state['pending'])} ファイル", also_print=False)

    return state


def _cleanup_empty(args) -> None:
    """空フォルダクリーンアップ"""
    if not args.quiet:
        print(f"\n🧹 空フォルダのクリーンアップ中...")
    deleted = cleanup_empty_folders(INDEX_DIR, quiet=args.quiet)
    if not args.quiet and deleted > 0:
        print(f"  ✅ {deleted} 個の空フォルダを削除しました")
    elif not args.quiet:
        print(f"  ℹ️ 空フォルダはありませんでした")
