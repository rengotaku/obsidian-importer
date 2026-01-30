"""
llm_import - LLM エクスポートデータをナレッジドキュメントに変換

Claude、ChatGPT 等の LLM エクスポートデータを読み込み、
Ollama を使用して知識を抽出し、Obsidian 形式のナレッジドキュメントを生成する。

Usage:
    python -m scripts.llm_import.cli --provider claude <input_dir>
    python -m scripts.llm_import.cli --provider claude --preview <input_dir>
"""

__version__ = "1.0.0"
