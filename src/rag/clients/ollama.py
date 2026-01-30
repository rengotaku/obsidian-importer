"""
Ollama Client - Ollama API クライアント

リモート Embedding サーバー (bge-m3) とローカル LLM (gpt-oss:20b) への接続機能を提供
"""
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    pass


# =============================================================================
# Connection Check
# =============================================================================


def check_connection(url: str, timeout: int = 5) -> tuple[bool, str | None]:
    """
    Ollama サーバーへの接続確認

    Args:
        url: Ollama サーバー URL (例: "http://localhost:11434")
        timeout: タイムアウト秒数

    Returns:
        (success: bool, error_message: str | None)
        成功時: (True, None)
        失敗時: (False, エラーメッセージ)
    """
    try:
        # Ollama の /api/tags エンドポイントで接続確認
        response = requests.get(f"{url}/api/tags", timeout=timeout)
        response.raise_for_status()
        return (True, None)
    except requests.exceptions.Timeout:
        return (False, f"Connection timeout after {timeout}s: {url}")
    except requests.exceptions.ConnectionError as e:
        return (False, f"Connection failed: {url} - {e}")
    except requests.exceptions.HTTPError as e:
        return (False, f"HTTP error: {url} - {e}")
    except requests.exceptions.RequestException as e:
        return (False, f"Request failed: {url} - {e}")


# =============================================================================
# Embedding
# =============================================================================


def get_embedding(
    text: str,
    model: str = "bge-m3",
    url: str = os.environ.get("OLLAMA_REMOTE_URL", "http://localhost:11434"),
    timeout: int = 30,
) -> tuple[list[float] | None, str | None]:
    """
    テキストの embedding を取得

    Args:
        text: 入力テキスト
        model: embedding モデル名
        url: Ollama サーバー URL
        timeout: タイムアウト秒数

    Returns:
        (embedding: list[float] | None, error: str | None)
        成功時: ([0.1, 0.2, ...], None)
        失敗時: (None, エラーメッセージ)
    """
    if not text or not text.strip():
        return (None, "Empty text provided")

    try:
        response = requests.post(
            f"{url}/api/embed",
            json={"model": model, "input": text},
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()

        # Ollama /api/embed returns {"embeddings": [[...]]}
        embeddings = data.get("embeddings")
        if embeddings and len(embeddings) > 0:
            return (embeddings[0], None)

        return (None, f"No embeddings in response: {data}")

    except requests.exceptions.Timeout:
        return (None, f"Embedding timeout after {timeout}s: {url}")
    except requests.exceptions.ConnectionError as e:
        return (None, f"Connection failed: {url} - {e}")
    except requests.exceptions.HTTPError as e:
        return (None, f"HTTP error: {url} - {e}")
    except json.JSONDecodeError as e:
        return (None, f"Invalid JSON response: {e}")
    except requests.exceptions.RequestException as e:
        return (None, f"Request failed: {url} - {e}")


# =============================================================================
# LLM Generation
# =============================================================================


def generate_response(
    prompt: str,
    model: str = "gpt-oss:20b",
    url: str = "http://localhost:11434",
    num_ctx: int = 65536,
    timeout: int = 120,
) -> tuple[str | None, str | None]:
    """
    LLM で回答を生成

    Args:
        prompt: プロンプト
        model: LLM モデル名
        url: Ollama サーバー URL
        num_ctx: コンテキストウィンドウサイズ
        timeout: タイムアウト秒数

    Returns:
        (response: str | None, error: str | None)
        成功時: ("生成されたテキスト", None)
        失敗時: (None, エラーメッセージ)
    """
    if not prompt or not prompt.strip():
        return (None, "Empty prompt provided")

    try:
        response = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": num_ctx},
            },
            timeout=timeout,
        )
        response.raise_for_status()

        data = response.json()

        # Ollama /api/generate returns {"response": "...", ...}
        generated = data.get("response")
        if generated is not None:
            return (generated, None)

        return (None, f"No response in data: {data}")

    except requests.exceptions.Timeout:
        return (None, f"Generation timeout after {timeout}s: {url}")
    except requests.exceptions.ConnectionError as e:
        return (None, f"Connection failed: {url} - {e}")
    except requests.exceptions.HTTPError as e:
        return (None, f"HTTP error: {url} - {e}")
    except json.JSONDecodeError as e:
        return (None, f"Invalid JSON response: {e}")
    except requests.exceptions.RequestException as e:
        return (None, f"Request failed: {url} - {e}")
