"""Ollama API client for obsidian-etl.

Pure function interface for LLM calls. Configuration via params dict.
Migrated from src/etl/utils/ollama.py with Kedro conventions.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def call_ollama(
    system_prompt: str,
    user_message: str,
    model: str = "gemma3:12b",
    base_url: str = "http://localhost:11434",
    num_ctx: int = 65536,
    temperature: float = 0.2,
    timeout: int = 120,
) -> tuple[str, str | None]:
    """Call Ollama API.

    Args:
        system_prompt: System prompt.
        user_message: User message.
        model: Model name.
        base_url: Ollama server base URL.
        num_ctx: Context window size.
        temperature: Sampling temperature.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (response_content, error_message).
        On success: (content, None).
        On failure: ("", error_message).
    """
    url = f"{base_url}/api/chat"
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
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("message", {}).get("content", "")
            return content, None
    except urllib.error.URLError as e:
        return "", f"Connection error: {e.reason}"
    except TimeoutError:
        return "", f"Timeout ({timeout}s)"
    except json.JSONDecodeError as e:
        return "", f"JSON parse error: {e}"
    except Exception as e:
        return "", f"API error: {e}"


def check_ollama_connection(base_url: str = "http://localhost:11434") -> tuple[bool, str | None]:
    """Check connection to Ollama server.

    Args:
        base_url: Ollama server base URL.

    Returns:
        Tuple of (connected, error_message).
    """
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return True, None
            return False, f"HTTP status: {resp.status}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"


# Code block fence pattern
_FENCE_PATTERN = re.compile(
    r"^\s*```(?:markdown)?\s*\n([\s\S]*?)\n\s*```\s*$",
    re.DOTALL,
)


def parse_markdown_response(response: str) -> tuple[dict, str | None]:
    """Parse markdown response into structured dict.

    Extracts title (H1), summary (## 要約), tags (## タグ), and content (## 内容) sections.

    Args:
        response: LLM markdown response text.

    Returns:
        Tuple of (parsed_dict, error_message).
    """
    if response is None or not str(response).strip():
        return {}, "Empty response"

    text = str(response).strip()

    # Strip code block fences
    match = _FENCE_PATTERN.match(text)
    if match:
        text = match.group(1).strip()

    # Split sections
    title, summary, tags, summary_content = _split_markdown_sections(text)

    return {"title": title, "summary": summary, "tags": tags, "summary_content": summary_content}, None


def _split_markdown_sections(text: str) -> tuple[str, str, list[str], str]:
    """Split markdown text into title, summary, tags, summary_content.

    Returns:
        Tuple of (title, summary, tags, summary_content).
    """
    lines = text.split("\n")

    title = ""
    summary = ""
    tags: list[str] = []
    summary_content = ""

    current_section: str | None = None
    section_lines: list[str] = []
    first_heading_text = ""
    first_heading_level = 0
    has_h1 = False

    def _flush_section() -> None:
        nonlocal title, summary, tags, summary_content
        body = "\n".join(section_lines).strip()
        if current_section == "summary":
            summary = body
        elif current_section == "tags":
            # Parse comma-separated tags
            if body:
                tags = [t.strip() for t in body.split(",") if t.strip()]
        elif current_section == "content":
            summary_content = body

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Sub-headings within content section stay in content
            if current_section == "content" and level >= 3:
                section_lines.append(line)
                continue

            _flush_section()
            section_lines = []

            if not first_heading_text:
                first_heading_text = heading_text
                first_heading_level = level

            if level == 1:
                has_h1 = True
                title = heading_text
                current_section = "title"
            elif level == 2 and heading_text == "要約":
                current_section = "summary"
            elif level == 2 and heading_text == "タグ":
                current_section = "tags"
            elif level == 2 and heading_text == "内容":
                current_section = "content"
            else:
                if current_section in ("summary", "tags", "content"):
                    section_lines.append(line)
                else:
                    current_section = "other_heading"
        else:
            section_lines.append(line)

    _flush_section()

    # Title fallback
    if not has_h1 and first_heading_text:
        if first_heading_level >= 2 and first_heading_text not in ("要約", "タグ", "内容"):
            title = first_heading_text

    # Plain text fallback
    if not first_heading_text:
        summary = text.strip()

    return title, summary, tags, summary_content
