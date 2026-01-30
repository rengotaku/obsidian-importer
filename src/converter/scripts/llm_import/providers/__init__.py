"""
llm_import.providers - プロバイダー固有の実装

各プロバイダー（Claude, ChatGPT 等）のパーサーを登録。
"""

from scripts.llm_import.providers.claude.parser import ClaudeParser

# プロバイダー登録
PROVIDERS: dict[str, type] = {
    "claude": ClaudeParser,
    # "chatgpt": ChatGPTParser,  # 将来実装
}
