"""
Parser - コマンドライン引数パーサー

argparseベースのCLIパーサーを提供。
"""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# CLI Parser
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """コマンドライン引数パーサーを作成"""
    parser = argparse.ArgumentParser(
        prog="ollama_normalizer",
        description="@index内のファイルをOllamaで分類・正規化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 単一ファイル処理
  python3 ollama_normalizer.py path/to/file.md

  # 全ファイル一括処理
  python3 ollama_normalizer.py --all

  # プレビューモード（移動なし）
  python3 ollama_normalizer.py --preview

  # 差分表示（処理前後を比較、変更なし）
  python3 ollama_normalizer.py path/to/file.md --diff

  # 処理状態確認
  python3 ollama_normalizer.py --status

  # 状態リセット
  python3 ollama_normalizer.py --all --reset
"""
    )

    # 位置引数
    parser.add_argument(
        "file",
        nargs="?",
        help="処理対象ファイルのパス"
    )

    # モード選択
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="@index内の全ファイルを処理"
    )
    mode_group.add_argument(
        "--preview",
        action="store_true",
        help="プレビューモード（実際の移動は行わない）"
    )
    mode_group.add_argument(
        "--status",
        action="store_true",
        help="処理状態を確認"
    )
    mode_group.add_argument(
        "--metrics",
        action="store_true",
        help="品質メトリクスを表示"
    )

    # オプション
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="詳細出力（除外ファイル一覧など）"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="処理状態をリセットして最初から実行"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="結果をJSON形式で出力"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="進捗表示を抑制"
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="処理前後の差分を表示（単一ファイル処理のみ）"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="大量ファイル処理時の確認プロンプトをスキップ"
    )
    parser.add_argument(
        "--no-cleanup-empty",
        action="store_true",
        dest="no_cleanup_empty",
        help="処理後の空フォルダ削除を無効化"
    )
    parser.add_argument(
        "--stage-debug",
        action="store_true",
        help="Multi-stage pipeline の個別ステージ結果を表示"
    )

    # セッション制御
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument(
        "--new",
        action="store_true",
        help="新規セッション開始（古いセッションは履歴として残る）"
    )
    session_group.add_argument(
        "--resume",
        action="store_true",
        help="中断セッションを続行"
    )

    return parser
