#!/usr/bin/env python3
"""
Ollama Normalizer for Obsidian @index files

@index内のファイルをOllamaで分類・正規化し、適切なVaultに配置

このファイルはエントリポイントとして機能し、実際の実装は
normalizer パッケージに含まれています。

Usage:
    python3 ollama_normalizer.py [args]
    python3 -m normalizer [args]

Examples:
    python3 ollama_normalizer.py --help
    python3 ollama_normalizer.py --status
    python3 ollama_normalizer.py --all
    python3 ollama_normalizer.py path/to/file.md
    python3 ollama_normalizer.py path/to/file.md --diff

標準ライブラリのみ使用
"""
import sys

from normalizer.cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
