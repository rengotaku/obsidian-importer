#!/usr/bin/env python3
"""
llm_import.cli - LLM エクスポートデータ処理 CLI

LLM エクスポートデータ（Claude, ChatGPT等）から知識を抽出し、
Obsidian ナレッジドキュメントに変換する。

Usage:
    python -m scripts.llm_import.cli --provider claude <input_dir>
    python -m scripts.llm_import.cli --provider claude <input_dir> --preview
    python -m scripts.llm_import.cli --provider claude <input_dir> --status

標準ライブラリのみ使用
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.llm_import.base import BaseConversation, BaseParser

from scripts.llm_import.base import sanitize_filename
from scripts.llm_import.common.error_writer import ErrorDetail, write_error_file
from scripts.llm_import.common.file_id import generate_file_id
from scripts.llm_import.common.folder_manager import FolderManager
from scripts.llm_import.common.knowledge_extractor import (
    KnowledgeExtractor,
    extract_file_id_from_frontmatter,
)
from scripts.llm_import.common.session_logger import SessionLogger
from scripts.llm_import.common.state import StateManager
from scripts.llm_import.providers import PROVIDERS


# =============================================================================
# Exit Codes (per contracts/cli-interface.md)
# =============================================================================

EXIT_SUCCESS = 0
EXIT_ARGUMENT_ERROR = 1
EXIT_INPUT_NOT_FOUND = 2
EXIT_OLLAMA_ERROR = 3
EXIT_PARTIAL_ERROR = 4
EXIT_ALL_FAILED = 5
EXIT_UNKNOWN_PROVIDER = 6


# =============================================================================
# Configuration
# =============================================================================


def _get_project_root() -> Path:
    """プロジェクトルート（Obsidian ルート）を取得

    .dev/scripts/llm_import/cli.py から Obsidian/ を取得
    """
    # このファイル: .dev/scripts/llm_import/cli.py
    # プロジェクトルート: Obsidian/
    return Path(__file__).resolve().parent.parent.parent.parent


def _get_staging_dir() -> Path:
    """ステージングディレクトリを取得"""
    return _get_project_root() / ".staging"


def _get_staging_index() -> Path:
    """標準出力先 .staging/@index を取得"""
    return _get_staging_dir() / "@index"


def _get_llm_exports_base() -> Path:
    """LLM エクスポート格納先を取得

    @index とは別の場所に配置し、og:organize との競合を避ける
    """
    return _get_staging_dir() / "@llm_exports"


# デフォルトの出力先（絶対パス）
DEFAULT_OUTPUT_DIR = _get_staging_index()

# LLM エクスポート格納先（絶対パス）
LLM_EXPORTS_BASE = _get_llm_exports_base()

# 短い会話のスキップ閾値（メッセージ数）
MIN_MESSAGES = 2


# =============================================================================
# CLI Entry Point
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """argparse パーサーを作成"""
    parser = argparse.ArgumentParser(
        description="LLM エクスポートデータから知識を抽出",
        prog="python -m scripts.llm_import.cli",
    )

    parser.add_argument(
        "input_dir",
        nargs="?",
        type=Path,
        help="エクスポートデータのディレクトリ",
    )

    parser.add_argument(
        "--provider", "-P",
        required=False,
        choices=list(PROVIDERS.keys()),
        help="プロバイダー名（必須: claude, chatgpt）",
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"出力ディレクトリ（デフォルト: {DEFAULT_OUTPUT_DIR}）",
    )

    parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="プレビューモード（ファイル変更なし）",
    )

    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="処理後に中間ファイルを削除しない",
    )

    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="処理状態を表示して終了",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="処理状態をリセット",
    )

    parser.add_argument(
        "--single",
        type=Path,
        help="単一ファイルのみ処理",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細ログ出力",
    )

    parser.add_argument(
        "--phase1-only",
        action="store_true",
        help="Phase 1（JSON→Markdown）のみ実行",
    )

    parser.add_argument(
        "--phase2-only",
        action="store_true",
        help="Phase 2（会話→ナレッジ）のみ実行",
    )

    parser.add_argument(
        "--phase2-limit",
        type=int,
        default=None,
        metavar="N",
        help="Phase 2 の処理件数を N 件に制限（Phase 1 はフル実行）",
    )

    # リトライ関連オプション
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="エラーファイルのリトライモード",
    )

    parser.add_argument(
        "--session",
        type=str,
        default=None,
        metavar="SESSION_ID",
        help="リトライ対象のセッション ID",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        metavar="SECONDS",
        help="Phase 2 処理のタイムアウト秒数（デフォルト: 120）",
    )

    return parser


def main() -> int:
    """メインエントリーポイント"""
    parser = create_parser()
    args = parser.parse_args()

    # --status モード
    if args.status:
        if not args.provider:
            print("❌ --status には --provider が必要です")
            return EXIT_ARGUMENT_ERROR
        return cmd_status(args.provider)

    # --reset オプション
    if args.reset:
        if not args.provider:
            print("❌ --reset には --provider が必要です")
            return EXIT_ARGUMENT_ERROR
        return cmd_reset(args.provider)

    # --retry-errors モード
    if args.retry_errors:
        if not args.provider:
            print("❌ --retry-errors には --provider が必要です")
            return EXIT_ARGUMENT_ERROR
        return cmd_retry(args)

    # プロバイダー必須チェック
    if not args.provider:
        print("❌ --provider オプションは必須です")
        parser.print_help()
        return EXIT_ARGUMENT_ERROR

    # 入力ディレクトリ必須チェック
    if not args.input_dir:
        print("❌ input_dir は必須です")
        parser.print_help()
        return EXIT_ARGUMENT_ERROR

    # プロバイダー存在チェック
    if args.provider not in PROVIDERS:
        print(f"❌ 未対応のプロバイダー: {args.provider}")
        print(f"   サポートされているプロバイダー: {', '.join(PROVIDERS.keys())}")
        return EXIT_UNKNOWN_PROVIDER

    # 入力ディレクトリ存在チェック
    if not args.input_dir.exists():
        print(f"❌ 入力ディレクトリが存在しません: {args.input_dir}")
        return EXIT_INPUT_NOT_FOUND

    # プレビューモード
    if args.preview:
        return cmd_preview(args)

    # メイン処理
    return cmd_process(args)


# =============================================================================
# Commands
# =============================================================================


def cmd_status(provider: str) -> int:
    """処理状態を表示"""
    state_manager = StateManager(provider, LLM_EXPORTS_BASE)
    stats = state_manager.get_stats()

    print(f"""
═══════════════════════════════════════════════════════════
  LLM Import - 処理状態 [{provider}]
═══════════════════════════════════════════════════════════

処理済み: {stats['total']} 会話
  ✅ 成功: {stats['success']}
  ⏭️  スキップ: {stats['skipped']}
  ❌ エラー: {stats['error']}

状態ファイル: {state_manager.state_file}
最終実行: {state_manager.state.last_run or 'なし'}
""")

    # エラーがあれば表示
    errors = state_manager.get_errors()
    if errors:
        print("エラー詳細:")
        for entry in errors[:5]:
            print(f"  - {entry.input_file}: {entry.error_message}")
        if len(errors) > 5:
            print(f"  ... 他 {len(errors) - 5} 件")

    return EXIT_SUCCESS


def cmd_reset(provider: str) -> int:
    """処理状態をリセット"""
    state_manager = StateManager(provider, LLM_EXPORTS_BASE)
    state_manager.reset()
    print(f"🔄 処理状態をリセットしました [{provider}]")
    return EXIT_SUCCESS


def cmd_retry(args) -> int:
    """エラーファイルのリトライ処理"""
    from scripts.llm_import.common.retry import (
        get_sessions_with_errors,
        validate_session,
        format_session_list,
        select_session_interactive,
        preview_retry,
        process_retry,
        load_errors_json,
        get_session_dir,
    )

    provider = args.provider
    session_id = args.session
    output_dir = args.output
    timeout = args.timeout
    verbose = args.verbose
    preview_mode = args.preview

    # タイムアウト検証
    if timeout < 1 or timeout > 600:
        print("❌ タイムアウトは 1-600 秒の範囲で指定してください")
        return EXIT_ARGUMENT_ERROR

    session_base_dir = get_session_dir()

    # セッション指定あり
    if session_id:
        valid, message = validate_session(session_id, session_base_dir)
        if not valid:
            print(f"❌ {message}")
            return EXIT_INPUT_NOT_FOUND

        # プレビューモード
        if preview_mode:
            print(preview_retry(session_id, session_base_dir))
            return EXIT_SUCCESS

        # リトライ実行
        return _execute_retry(
            session_id, provider, output_dir, timeout, verbose, session_base_dir, args
        )

    # セッション未指定: エラーのあるセッション一覧を取得
    sessions = get_sessions_with_errors(session_base_dir)

    if not sessions:
        print("✅ リトライ対象のセッションがありません")
        return EXIT_SUCCESS

    # 1件のみなら自動選択
    auto_selected = select_session_interactive(sessions)
    if auto_selected:
        print(f"🎯 自動選択: {auto_selected.session_id} ({auto_selected.error_count} 件のエラー)")

        # プレビューモード
        if preview_mode:
            print(preview_retry(auto_selected.session_id, session_base_dir))
            return EXIT_SUCCESS

        return _execute_retry(
            auto_selected.session_id, provider, output_dir, timeout, verbose, session_base_dir, args
        )

    # 複数のセッションがある場合は一覧表示
    print(format_session_list(sessions))
    return EXIT_SUCCESS


def _execute_retry(
    session_id: str,
    provider: str,
    output_dir: Path,
    timeout: int,
    verbose: bool,
    session_base_dir: Path,
    args,
) -> int:
    """リトライ処理を実行（cmd_process を流用）

    Args:
        session_id: リトライ元セッション ID
        provider: プロバイダー名
        output_dir: 出力ディレクトリ
        timeout: タイムアウト秒数
        verbose: 詳細ログ出力
        session_base_dir: @session ディレクトリ
        args: argparse の Namespace

    Returns:
        終了コード
    """
    from scripts.llm_import.common.retry import (
        load_errors_json,
        find_conversations_json,
    )

    # エラーからリトライ対象IDを取得
    session_dir = session_base_dir / session_id
    errors = load_errors_json(session_dir)
    retry_ids = {e.file for e in errors}

    # ヘッダー出力
    print("=" * 80)
    print("RETRY SESSION")
    print("=" * 80)
    print(f"Source Session: {session_id}")
    print(f"Error Count: {len(retry_ids)}")
    print(f"Retry Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # input_dir を conversations.json の親ディレクトリから取得
    conversations_json = find_conversations_json(provider)
    if not conversations_json:
        print(f"❌ {provider} の conversations.json が見つかりません")
        return EXIT_INPUT_NOT_FOUND

    # args に必要な属性を設定
    args.input_dir = conversations_json.parent
    args.phase1_only = False
    args.phase2_only = False
    args.phase2_limit = None
    args.no_delete = True  # リトライ時は中間ファイル削除しない

    # cmd_process を呼び出し（1回のパースで全会話を取得）
    return cmd_process(
        args,
        retry_ids=retry_ids,
        source_session=session_id,
    )


def cmd_preview(args) -> int:
    """プレビューモード"""
    provider = args.provider
    input_dir = args.input_dir

    # パーサーを取得
    parser_class = PROVIDERS[provider]
    parser: BaseParser = parser_class()

    # パース
    try:
        conversations = parser.parse(input_dir)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return EXIT_INPUT_NOT_FOUND
    except Exception as e:
        print(f"❌ パースエラー: {e}")
        return EXIT_ARGUMENT_ERROR

    # 状態マネージャ
    state_manager = StateManager(provider, LLM_EXPORTS_BASE)

    # フィルタリング
    to_process = []
    to_skip = []
    for conv in conversations:
        if state_manager.is_processed(conv.id):
            continue
        if len(conv.messages) < MIN_MESSAGES:
            to_skip.append(conv)
        else:
            to_process.append(conv)

    print(f"""
═══════════════════════════════════════════════════════════
  LLM Import - プレビュー [{provider}]
═══════════════════════════════════════════════════════════

処理対象: {len(conversations)} 会話
  📄 処理予定: {len(to_process)}
  ⏭️  スキップ予定: {len(to_skip)} (短い会話)
  ✅ 処理済み: {len(conversations) - len(to_process) - len(to_skip)}
""")

    # サンプル出力
    if to_process:
        sample = to_process[0]
        print(f"""サンプル出力 (1/{len(to_process)}):
---
ファイル: {_generate_filename(sample)}
プロバイダー: {provider}
タイトル: {sample.title}
メッセージ数: {len(sample.messages)}
作成日: {sample.created_at[:10]}
---

実行するには --preview オプションを外してください
""")

    return EXIT_SUCCESS


def cmd_process(
    args,
    retry_ids: set[str] | None = None,
    source_session: str | None = None,
) -> int:
    """メイン処理（Phase 1 → 2）with SessionLogger

    Args:
        args: argparse の Namespace
        retry_ids: リトライ対象の会話IDセット（指定時はこのIDのみ処理）
        source_session: リトライ元セッションID（リトライ時のみ指定）
    """
    provider = args.provider
    input_dir = args.input_dir
    output_dir = args.output
    verbose = args.verbose
    phase1_only = args.phase1_only
    phase2_only = args.phase2_only
    phase2_limit = args.phase2_limit
    no_delete = args.no_delete

    start_time = time.time()

    # パーサーを取得
    parser_class = PROVIDERS[provider]
    parser: BaseParser = parser_class()

    # 状態マネージャ
    state_manager = StateManager(provider, LLM_EXPORTS_BASE)

    # 知識抽出器
    extractor = KnowledgeExtractor()

    # パース
    try:
        conversations = parser.parse(input_dir)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return EXIT_INPUT_NOT_FOUND
    except Exception as e:
        print(f"❌ パースエラー: {e}")
        return EXIT_ARGUMENT_ERROR

    # フィルタリング
    to_process = []
    for conv in conversations:
        # リトライモード: 指定IDのみ処理
        if retry_ids is not None:
            if conv.id in retry_ids:
                to_process.append(conv)
            continue

        # 通常モード: 処理済み・短い会話を除外
        if state_manager.is_processed(conv.id):
            if verbose:
                print(f"⏭️  処理済み: {conv.title}")
            continue
        if len(conv.messages) < MIN_MESSAGES:
            state_manager.add_entry(
                conversation_id=conv.id,
                input_file="",
                output_file="",
                status="skipped",
                skip_reason=f"メッセージ数が少ない ({len(conv.messages)} < {MIN_MESSAGES})",
            )
            if verbose:
                print(f"⏭️  スキップ: {conv.title} (メッセージ数: {len(conv.messages)})")
            continue
        to_process.append(conv)

    if not to_process:
        print("✅ 処理対象の会話がありません")
        state_manager.save()
        return EXIT_SUCCESS

    # ============================================================
    # SessionLogger 初期化・セッション開始 (T018-T019)
    # ============================================================
    # FolderManager で新しいフォルダ構造を使用
    session_base_dir = _get_staging_dir() / "@session"
    folder_manager = FolderManager(session_base_dir)

    session_logger = SessionLogger(
        provider=provider,
        total_files=len(to_process),
        prefix="import",
        source_session=source_session,
        folder_manager=folder_manager,
    )
    session_dir = session_logger.start_session()
    session_paths = session_logger.get_paths()

    phase2_info = f" (Phase 2: 最大 {phase2_limit} 件)" if phase2_limit else ""
    if session_dir:
        session_logger.log(f"処理対象: {len(to_process)} 会話{phase2_info}")
        session_logger.log(f"セッション: {session_dir}")
    else:
        # セッション作成失敗時は従来のヘッダー出力
        print(f"""
═══════════════════════════════════════════════════════════
  LLM Import - 処理開始 [{provider}]
═══════════════════════════════════════════════════════════

処理対象: {len(to_process)} 会話{phase2_info}
""")

    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1 出力先: 新構造では session_paths["parsed"]、フォールバックはレガシー
    if session_paths and "parsed" in session_paths:
        parsed_dir = session_paths["parsed"]
    else:
        parsed_dir = parser.get_output_dir(LLM_EXPORTS_BASE)
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # エラー出力先
    errors_dir = session_paths.get("errors") if session_paths else None

    # 処理結果
    success_count = 0
    error_count = 0
    phase2_count = 0  # Phase 2 処理件数

    for i, conv in enumerate(to_process, 1):
        conv_start_time = time.time()
        phase1_ok = False
        phase2_ok: bool | None = None
        phase1_path: Path | None = None

        try:
            # Phase 1: JSON → Markdown (T024)
            if not phase2_only:
                phase1_start = time.time()
                phase1_filename = _generate_filename(conv) + ".md"
                phase1_path = parsed_dir / phase1_filename

                # T008: Phase 1 で file_id を生成（コンテンツ + パスから計算）
                # 一度 file_id なしで markdown 生成 → file_id 計算 → 再生成
                markdown_without_id = parser.to_markdown(conv)
                relative_path = phase1_path.relative_to(parsed_dir.parent.parent)
                phase1_file_id = generate_file_id(markdown_without_id, relative_path)
                markdown = parser.to_markdown(conv, file_id=phase1_file_id)

                phase1_path.write_text(markdown, encoding="utf-8")
                phase1_ok = True

                # T026: log_stage for Phase 1 (T015: file_id を渡す)
                phase1_ms = int((time.time() - phase1_start) * 1000)
                session_logger.log_stage(
                    filename=conv.title,
                    stage="phase1",
                    timing_ms=phase1_ms,
                    file_id=phase1_file_id,
                )

                if verbose:
                    print(f"  Phase 1: {phase1_path}")

            if phase1_only:
                state_manager.add_entry(
                    conversation_id=conv.id,
                    input_file=str(phase1_path) if phase1_path else "",
                    output_file="",
                    status="success",
                )
                success_count += 1
                # T038: add_processed
                session_logger.add_processed(
                    file=conv.id,
                    output=str(phase1_path) if phase1_path else "",
                )
                # T020: log_progress
                elapsed_sec = time.time() - conv_start_time
                session_logger.log_progress(
                    current=i,
                    title=conv.title,
                    phase1_ok=phase1_ok,
                    phase2_ok=None,
                    elapsed_sec=elapsed_sec,
                )
                continue

            # Phase 2 件数制限チェック
            if phase2_limit is not None and phase2_count >= phase2_limit:
                state_manager.add_entry(
                    conversation_id=conv.id,
                    input_file=str(phase1_path) if phase1_path else "",
                    output_file="",
                    status="success",
                )
                success_count += 1
                # T038: add_pending (Phase 2 制限)
                session_logger.add_pending(
                    file=conv.id,
                    reason="phase2_limit",
                )
                # T026: log_stage for skipped Phase 2
                session_logger.log_stage(
                    filename=conv.title,
                    stage="phase2",
                    timing_ms=0,
                    skipped_reason="phase2_limit",
                )
                elapsed_sec = time.time() - conv_start_time
                session_logger.log_progress(
                    current=i,
                    title=conv.title,
                    phase1_ok=phase1_ok,
                    phase2_ok=None,
                    elapsed_sec=elapsed_sec,
                )
                if verbose:
                    print(f"  Phase 2 スキップ (制限: {phase2_limit} 件)")
                continue

            # Phase 2: 会話 → ナレッジ (T025)
            phase2_start = time.time()

            # チャンク分割判定
            if extractor.should_chunk(conv):
                # チャンク分割処理
                chunk_results = extractor.extract_chunked(conv)
                phase2_ms = int((time.time() - phase2_start) * 1000)

                chunk_success = 0
                chunk_error = 0
                output_files = []

                for filename, result in chunk_results:
                    if result.success:
                        # チャンク出力
                        document = result.document
                        output_filename = sanitize_filename(filename[:-3]) + ".md"  # Remove .md, re-add
                        output_path = output_dir / output_filename

                        # file_id を生成して設定（T012: 各チャンクに異なる file_id）
                        content_for_hash = document.to_markdown()
                        relative_path = output_path.relative_to(output_dir.parent.parent)
                        document.file_id = generate_file_id(content_for_hash, relative_path)

                        after_content = document.to_markdown()
                        output_path.write_text(after_content, encoding="utf-8")
                        output_files.append(str(output_path))
                        chunk_success += 1
                        if verbose:
                            print(f"  Phase 2: {output_path}")
                    else:
                        chunk_error += 1
                        print(f"  ❌ チャンク処理エラー ({filename}): {result.error}")

                # 全チャンク失敗
                if chunk_success == 0:
                    phase2_ok = False
                    session_logger.log_stage(
                        filename=conv.title,
                        stage="phase2",
                        timing_ms=phase2_ms,
                        skipped_reason=f"全 {len(chunk_results)} チャンク失敗",
                    )
                    state_manager.add_entry(
                        conversation_id=conv.id,
                        input_file=str(phase1_path) if phase1_path else "",
                        output_file="",
                        status="error",
                        error_message=f"全 {len(chunk_results)} チャンク失敗",
                    )
                    session_logger.add_error(
                        file=conv.id,
                        error=f"全 {len(chunk_results)} チャンク失敗",
                        stage="phase2",
                    )
                    error_count += 1
                else:
                    phase2_ok = True
                    # T016: チャンク成功時は最初のチャンクの file_id を使用
                    first_chunk_file_id = None
                    for _, result in chunk_results:
                        if result.success and result.document:
                            first_chunk_file_id = result.document.file_id
                            break
                    session_logger.log_stage(
                        filename=conv.title,
                        stage="phase2",
                        timing_ms=phase2_ms,
                        file_id=first_chunk_file_id,
                    )
                    state_manager.add_entry(
                        conversation_id=conv.id,
                        input_file=str(phase1_path) if phase1_path else "",
                        output_file=",".join(output_files),
                        status="success" if chunk_error == 0 else "partial",
                        file_id=first_chunk_file_id,
                    )
                    session_logger.add_processed(
                        file=conv.id,
                        output=",".join(output_files),
                    )
                    success_count += 1
                    phase2_count += 1

                    if chunk_error > 0:
                        print(f"  ⚠️  {chunk_success}/{len(chunk_results)} チャンク成功")

                elapsed_sec = time.time() - conv_start_time
                session_logger.log_progress(
                    current=i,
                    title=conv.title,
                    phase1_ok=phase1_ok,
                    phase2_ok=phase2_ok,
                    elapsed_sec=elapsed_sec,
                )
                continue

            # 通常処理（チャンク分割なし）
            result = extractor.extract(conv)
            phase2_ms = int((time.time() - phase2_start) * 1000)

            if not result.success:
                phase2_ok = False
                # T026: log_stage for Phase 2 error
                session_logger.log_stage(
                    filename=conv.title,
                    stage="phase2",
                    timing_ms=phase2_ms,
                    skipped_reason=result.error,
                )
                print(f"  ❌ 知識抽出エラー: {result.error}")
                state_manager.add_entry(
                    conversation_id=conv.id,
                    input_file=str(phase1_path) if phase1_path else "",
                    output_file="",
                    status="error",
                    error_message=result.error,
                )
                # T038: add_error
                session_logger.add_error(
                    file=conv.id,
                    error=result.error or "Unknown error",
                    stage="phase2",
                )

                # エラー詳細ファイル出力 (021-import-error-debug)
                if errors_dir:
                    # 元の会話内容を取得
                    original_content = parser.to_markdown(conv)
                    error_detail = ErrorDetail(
                        session_id=session_dir.name if session_dir else "unknown",
                        conversation_id=conv.id,
                        conversation_title=conv.title,
                        timestamp=datetime.now(),
                        error_type="json_parse" if "JSON" in (result.error or "") else "extraction",
                        error_message=result.error or "Unknown error",
                        original_content=original_content,
                        llm_prompt=result.user_prompt or "",
                        llm_output=result.raw_response,
                        stage="phase2",
                    )
                    write_error_file(error_detail, errors_dir)

                error_count += 1
                elapsed_sec = time.time() - conv_start_time
                session_logger.log_progress(
                    current=i,
                    title=conv.title,
                    phase1_ok=phase1_ok,
                    phase2_ok=phase2_ok,
                    elapsed_sec=elapsed_sec,
                )
                continue

            phase2_ok = True

            # Phase 2 出力
            document = result.document
            output_filename = sanitize_filename(document.title) + ".md"
            output_path = output_dir / output_filename

            # T022: file_id を parsed ファイルから継承、なければ新規生成
            inherited_file_id: str | None = None
            if phase1_path and phase1_path.exists():
                parsed_content = phase1_path.read_text(encoding="utf-8")
                inherited_file_id = extract_file_id_from_frontmatter(parsed_content)

            if inherited_file_id:
                # Phase 1 からの継承
                document.file_id = inherited_file_id
            else:
                # 新規生成（T011: ファイル書き込み前に生成）
                content_for_hash = document.to_markdown()
                relative_path = output_path.relative_to(output_dir.parent.parent)
                document.file_id = generate_file_id(content_for_hash, relative_path)

            after_content = document.to_markdown()

            # 中間ファイル保持: session output/ に書き込み
            session_output_dir = session_paths.get("output") if session_paths else None
            if session_output_dir:
                session_output_path = session_output_dir / output_filename
                session_output_path.write_text(after_content, encoding="utf-8")

            # @index/ にコピー（最終出力）
            output_path.write_text(after_content, encoding="utf-8")

            # 差分計算（before: Phase 1出力, after: Phase 2出力）
            before_chars = None
            if phase1_path and phase1_path.exists():
                before_chars = len(phase1_path.read_text(encoding="utf-8"))
            after_chars = len(after_content)

            # T026: log_stage for Phase 2 success (T016: file_id を渡す)
            session_logger.log_stage(
                filename=conv.title,
                stage="phase2",
                timing_ms=phase2_ms,
                before_chars=before_chars,
                after_chars=after_chars,
                file_id=document.file_id,
            )

            if verbose:
                print(f"  Phase 2: {output_path}")

            state_manager.add_entry(
                conversation_id=conv.id,
                input_file=str(phase1_path) if phase1_path else "",
                output_file=str(output_path),
                status="success",
                file_id=document.file_id,
            )
            # T038: add_processed
            session_logger.add_processed(
                file=conv.id,
                output=str(output_path),
            )
            success_count += 1
            phase2_count += 1

            # T020: log_progress
            elapsed_sec = time.time() - conv_start_time
            session_logger.log_progress(
                current=i,
                title=conv.title,
                phase1_ok=phase1_ok,
                phase2_ok=phase2_ok,
                elapsed_sec=elapsed_sec,
            )

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            state_manager.add_entry(
                conversation_id=conv.id,
                input_file="",
                output_file="",
                status="error",
                error_message=str(e),
            )
            # T038: add_error
            session_logger.add_error(
                file=conv.id,
                error=str(e),
                stage="phase1" if not phase1_ok else "phase2",
            )
            error_count += 1
            elapsed_sec = time.time() - conv_start_time
            session_logger.log_progress(
                current=i,
                title=conv.title,
                phase1_ok=phase1_ok,
                phase2_ok=False,
                elapsed_sec=elapsed_sec,
            )

    # 状態保存
    state_manager.save()

    elapsed = time.time() - start_time

    # T039: finalize() でサマリー出力
    session_logger.finalize(elapsed_seconds=elapsed)

    # 中間ファイル削除は行わない (021-import-error-debug)
    # parsed/ と output/ のファイルはデバッグ用に保持
    # --no-delete フラグは後方互換性のため残すが no-op

    # 終了コード
    if error_count == len(to_process):
        return EXIT_ALL_FAILED
    if error_count > 0:
        return EXIT_PARTIAL_ERROR
    return EXIT_SUCCESS


# =============================================================================
# Helper Functions
# =============================================================================


def _generate_filename(conv: BaseConversation) -> str:
    """会話からファイル名を生成（日付プレフィックスなし）"""
    # タイトルから日付プレフィックス (YYYY-MM-DD_) を除去
    title = conv.title
    if title and len(title) > 10 and title[10:11] == "_":
        # 日付プレフィックスがある場合は除去
        potential_date = title[:10]
        if potential_date.replace("-", "").isdigit():
            title = title[11:]
    return sanitize_filename(title, max_length=60)


def _format_duration(seconds: float) -> str:
    """秒数を人間可読な形式に変換"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}分{secs}秒"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}時間{mins}分{secs}秒"


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    sys.exit(main())
