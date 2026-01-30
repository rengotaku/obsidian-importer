"""
src.etl.utils.ollama - Ollama API クライアント

Ollama API の呼び出しとマークダウンレスポンスのパースを行う。
src/converter/scripts/llm_import/common/ollama.py からコピー。
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
    temperature: float = 0.2,
    timeout: int = API_TIMEOUT,
) -> tuple[str, str | None]:
    """
    Ollama API を呼び出し

    Args:
        system_prompt: システムプロンプト
        user_message: ユーザーメッセージ
        model: 使用するモデル（デフォルト: gpt-oss:20b）
        num_ctx: コンテキストウィンドウサイズ（デフォルト: 65536）
        temperature: サンプリング温度（デフォルト: 0.2、0.0-2.0）
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
        "options": {"num_ctx": num_ctx, "temperature": temperature},
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


def parse_markdown_response(response: str) -> tuple[dict, str | None]:
    """
    マークダウンレスポンスを構造化 dict に変換。

    処理手順:
    1. 空入力チェック
    2. コードブロックフェンス除去 (```markdown ... ``` or ``` ... ```)
    3. 見出し検出 (#, ##, ###)
    4. セクション分割: title(#), summary(## 要約), content(## 内容)
    5. dict 構築

    Args:
        response: LLM からのマークダウン応答テキスト

    Returns:
        tuple[dict, str | None]: (parsed dict, error_message or None)
    """
    # 空入力チェック
    if response is None or not str(response).strip():
        return {}, "空の応答です"

    text = str(response).strip()

    # コードブロックフェンス除去
    text = _strip_code_block_fence(text)

    # セクション分割
    title, summary, summary_content = _split_markdown_sections(text)

    result = {
        "title": title,
        "summary": summary,
        "summary_content": summary_content,
    }

    return result, None


# コードブロックフェンス除去用正規表現
_FENCE_PATTERN = re.compile(
    r"^\s*```(?:markdown)?\s*\n([\s\S]*?)\n\s*```\s*$",
    re.DOTALL,
)


def _strip_code_block_fence(text: str) -> str:
    """外側のコードブロックフェンスを除去する"""
    match = _FENCE_PATTERN.match(text)
    if match:
        return match.group(1).strip()
    return text


def _split_markdown_sections(text: str) -> tuple[str, str, str]:
    """
    マークダウンテキストを title, summary, summary_content に分割。

    Returns:
        tuple[str, str, str]: (title, summary, summary_content)
    """
    lines = text.split("\n")

    title = ""
    summary = ""
    summary_content = ""

    # セクションを検出して分割
    # current_section: None, "title", "summary", "content", "other_heading"
    current_section: str | None = None
    section_lines: list[str] = []
    first_heading_text = ""  # H1 がない場合のフォールバック用
    first_heading_level = 0
    has_h1 = False
    has_summary_section = False
    has_content_section = False

    def _flush_section() -> None:
        nonlocal title, summary, summary_content
        body = "\n".join(section_lines).strip()
        if current_section == "title":
            pass  # title は見出し行で設定済み
        elif current_section == "summary":
            summary = body
        elif current_section == "content":
            summary_content = body

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # content セクション内のサブ見出し（### 以下）はそのまま content に含める
            if current_section == "content" and level >= 3:
                section_lines.append(line)
                continue

            # 前のセクションを保存
            _flush_section()
            section_lines = []

            # 最初の見出しを記録（フォールバック用）
            if not first_heading_text:
                first_heading_text = heading_text
                first_heading_level = level

            if level == 1:
                has_h1 = True
                title = heading_text
                current_section = "title"
            elif level == 2 and heading_text == "要約":
                has_summary_section = True
                current_section = "summary"
            elif level == 2 and heading_text == "内容":
                has_content_section = True
                current_section = "content"
            else:
                # サブ見出しまたは不明な ## セクション
                if current_section in ("summary", "content"):
                    section_lines.append(line)
                else:
                    current_section = "other_heading"
        else:
            section_lines.append(line)

    # 最後のセクションを保存
    _flush_section()

    # タイトルのフォールバック: H1 がない場合
    if not has_h1 and first_heading_text:
        # 最初の ## が「要約」「内容」でなければタイトルとして使用
        if first_heading_level >= 2 and first_heading_text not in ("要約", "内容"):
            title = first_heading_text

    # プレーンテキストフォールバック（見出しなし）
    if not first_heading_text:
        # 見出しが全くない場合、全体を summary として扱う
        summary = text.strip()

    return title, summary, summary_content
