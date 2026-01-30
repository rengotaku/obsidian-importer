"""
Contract: parse_json_response

機能: LLM応答文字列からJSONを抽出・パース

入力: response (str) - LLMからの生の応答テキスト
出力: tuple[dict, str | None] - (パース済みdict, エラーメッセージ or None)

既存APIとの互換性を維持。
"""

from typing import TypedDict


class ParseError(TypedDict):
    """パースエラーの詳細"""
    type: str  # "no_json" | "incomplete" | "invalid" | "decode_error"
    message: str
    position: int | None
    context: str | None


def parse_json_response(response: str) -> tuple[dict, str | None]:
    """
    Ollama応答からJSONを抽出・パース（堅牢版）

    抽出優先順位:
    1. Markdownコードブロック内のJSON
    2. 括弧バランス追跡による最初の完全なJSONオブジェクト

    Args:
        response: LLMからの生の応答テキスト

    Returns:
        tuple: (パース済みdict, エラーメッセージ or None)

    Examples:
        >>> parse_json_response('{"genre": "エンジニア"}')
        ({'genre': 'エンジニア'}, None)

        >>> parse_json_response('結果: {"genre": "ビジネス"} 以上です')
        ({'genre': 'ビジネス'}, None)

        >>> parse_json_response('```json\n{"genre": "経済"}\n```')
        ({'genre': '経済'}, None)

        >>> parse_json_response('JSONなし')
        ({}, 'JSON形式の応答がありません')
    """
    ...


def extract_json_from_code_block(response: str) -> str | None:
    """
    Markdownコードブロックからjsonを抽出

    Args:
        response: LLMからの応答テキスト

    Returns:
        抽出されたJSON文字列、見つからなければNone
    """
    ...


def extract_first_json_object(text: str) -> str | None:
    """
    括弧バランス追跡で最初の完全なJSONオブジェクトを抽出

    Args:
        text: 検索対象のテキスト

    Returns:
        抽出されたJSON文字列、見つからなければNone
    """
    ...


def format_parse_error(error: Exception, json_str: str) -> str:
    """
    パースエラーを人間可読な形式でフォーマット

    Args:
        error: JSONDecodeErrorなどの例外
        json_str: パースを試みたJSON文字列

    Returns:
        エラーメッセージ（位置とコンテキスト含む）
    """
    ...
