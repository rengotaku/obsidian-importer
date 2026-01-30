"""
Obsidian Normalizer Package

@index内のファイルをOllamaで分類・正規化し、適切なVaultに配置するパッケージ

Modules:
    config: 設定値、定数、パス定義
    models: TypedDict、型定義
    validators: タイトル、タグ、フォーマット検証
    detection: 英語文書判定
    pipeline: LLMパイプライン（プロンプト、ステージ、実行）
    io: ファイル操作、セッション管理、Ollama API
    state: 処理状態管理
    processing: 単一/バッチファイル処理
    output: 結果フォーマット、差分表示
    cli: コマンドライン引数、コマンド実装

Usage:
    python -m normalizer --help
    python -m normalizer path/to/file.md
    python -m normalizer --all
    python -m normalizer --status
"""

__version__ = "2.0.0"

# CLI entry point
from normalizer.cli.commands import main

__all__ = ["main", "__version__"]
