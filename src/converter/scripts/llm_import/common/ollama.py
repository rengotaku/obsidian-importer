"""
llm_import.common.ollama - Ollama API クライアント

Ollama API の呼び出しと JSON レスポンスのパースを行う。
normalizer/io/ollama.py を参照して実装。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# Configuration
# =============================================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"
API_TIMEOUT = 120


# =============================================================================
# Ollama API
# =============================================================================


def call_ollama(
    system_prompt: str,
    user_message: str,
    model: str = MODEL,
    num_ctx: int = 65536,
    timeout: int = API_TIMEOUT,
) -> tuple[str, str | None]:
    """
    Ollama API を呼び出し

    Args:
        system_prompt: システムプロンプト
        user_message: ユーザーメッセージ
        model: 使用するモデル（デフォルト: gpt-oss:20b）
        num_ctx: コンテキストウィンドウサイズ（デフォルト: 65536）
        timeout: タイムアウト秒数（デフォルト: 120）

    Returns:
        tuple: (response_content, error_message)
            - 成功時: (レスポンス内容, None)
            - 失敗時: ("", エラーメッセージ)
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"num_ctx": num_ctx},
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            return content, None
    except urllib.error.URLError as e:
        return "", f"接続エラー: {e.reason}"
    except TimeoutError:
        return "", f"タイムアウト ({timeout}秒)"
    except json.JSONDecodeError as e:
        return "", f"JSONパースエラー: {e}"
    except Exception as e:
        return "", f"APIエラー: {e}"


def check_ollama_connection() -> tuple[bool, str | None]:
    """
    Ollama サーバーへの接続を確認

    Returns:
        tuple: (接続成功, エラーメッセージ)
    """
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return True, None
            return False, f"HTTPステータス: {resp.status}"
    except urllib.error.URLError as e:
        return False, f"接続エラー: {e.reason}"
    except Exception as e:
        return False, f"エラー: {e}"


# =============================================================================
# JSON Parsing Helpers
# =============================================================================

# コードブロック抽出用正規表現
CODE_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```")


def extract_json_from_code_block(response: str) -> str | None:
    """
    Markdown コードブロックから JSON を抽出

    Args:
        response: LLM からの応答テキスト

    Returns:
        抽出された JSON 文字列、見つからなければ None
    """
    match = CODE_BLOCK_PATTERN.search(response)
    return match.group(1) if match else None


def extract_first_json_object(text: str) -> str | None:
    """
    括弧バランス追跡で最初の完全な JSON オブジェクトを抽出

    Args:
        text: 検索対象のテキスト

    Returns:
        抽出された JSON 文字列、見つからなければ None
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
        if char == "\\" and in_string:
            escape = True
            continue
        if char == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def format_parse_error(error: json.JSONDecodeError, json_str: str) -> str:
    """
    パースエラーを人間可読な形式でフォーマット

    Args:
        error: JSONDecodeError 例外
        json_str: パースを試みた JSON 文字列

    Returns:
        エラーメッセージ（位置とコンテキスト含む）
    """
    pos = error.pos if hasattr(error, "pos") else 0
    context_start = max(0, pos - 30)
    context_end = min(len(json_str), pos + 30)
    context = json_str[context_start:context_end]
    return f"JSONパースエラー: {error.msg} (位置 {pos})\nコンテキスト: ...{context}..."


def parse_json_response(response: str) -> tuple[dict, str | None]:
    """
    Ollama 応答から JSON を抽出・パース（堅牢版）

    抽出優先順位:
    1. Markdown コードブロック内の JSON
    2. 括弧バランス追跡による最初の完全な JSON オブジェクト

    Args:
        response: LLM からの生の応答テキスト

    Returns:
        tuple: (パース済み dict, エラーメッセージ or None)
    """
    # 空の応答チェック
    if not response or not response.strip():
        return {}, "空の応答です"

    # コードブロックを優先的に抽出
    json_str = extract_json_from_code_block(response)

    # コードブロックがなければ括弧バランス追跡
    if not json_str:
        json_str = extract_first_json_object(response)

    if not json_str:
        return {}, "JSON形式の応答がありません"

    # JSON パース
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        return {}, format_parse_error(e, json_str)
