"""
Ollama API - Ollama API通信とJSONパース

Ollama APIの呼び出しとレスポンスの堅牢なJSONパースを行う。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import OLLAMA_URL, MODEL, API_TIMEOUT


# =============================================================================
# Ollama API
# =============================================================================


def call_ollama(system_prompt: str, user_message: str, num_ctx: int = 16384) -> tuple[str, str | None]:
    """
    Ollama APIを呼び出し

    Args:
        system_prompt: システムプロンプト
        user_message: ユーザーメッセージ
        num_ctx: コンテキストウィンドウサイズ（デフォルト16384）

    Returns:
        tuple: (response_content, error_message)
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {
            "num_ctx": num_ctx
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            return content, None
    except urllib.error.URLError as e:
        return "", f"接続エラー: {e.reason}"
    except TimeoutError:
        return "", f"タイムアウト ({API_TIMEOUT}秒)"
    except json.JSONDecodeError as e:
        return "", f"JSONパースエラー: {e}"
    except Exception as e:
        return "", f"APIエラー: {e}"


# =============================================================================
# JSON Parsing Helpers (Robust Implementation)
# =============================================================================

# コードブロック抽出用正規表現
# DOTALLで改行をまたいでマッチ、jsonラベル有無両対応
CODE_BLOCK_PATTERN = re.compile(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```')


def extract_json_from_code_block(response: str) -> str | None:
    """
    Markdownコードブロックからjsonを抽出

    Args:
        response: LLMからの応答テキスト

    Returns:
        抽出されたJSON文字列、見つからなければNone
    """
    match = CODE_BLOCK_PATTERN.search(response)
    return match.group(1) if match else None


def extract_first_json_object(text: str) -> str | None:
    """
    括弧バランス追跡で最初の完全なJSONオブジェクトを抽出

    Args:
        text: 検索対象のテキスト

    Returns:
        抽出されたJSON文字列、見つからなければNone
    """
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if char == '\\' and in_string:
            escape = True
            continue
        if char == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


def format_parse_error(error: json.JSONDecodeError, json_str: str) -> str:
    """
    パースエラーを人間可読な形式でフォーマット

    Args:
        error: JSONDecodeError例外
        json_str: パースを試みたJSON文字列

    Returns:
        エラーメッセージ（位置とコンテキスト含む）
    """
    pos = error.pos if hasattr(error, 'pos') else 0
    context_start = max(0, pos - 30)
    context_end = min(len(json_str), pos + 30)
    context = json_str[context_start:context_end]
    return f"JSONパースエラー: {error.msg} (位置 {pos})\nコンテキスト: ...{context}..."


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

        >>> parse_json_response('```json\\n{"genre": "経済"}\\n```')
        ({'genre': '経済'}, None)
    """
    # T008: 空の応答チェック
    if not response or not response.strip():
        return {}, "空の応答です"

    # T009: コードブロックを優先的に抽出
    json_str = extract_json_from_code_block(response)

    # T010: コードブロックがなければ括弧バランス追跡
    if not json_str:
        json_str = extract_first_json_object(response)

    if not json_str:
        return {}, "JSON形式の応答がありません"

    # JSONパース
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        # T011: 改善されたエラーメッセージ
        return {}, format_parse_error(e, json_str)
