#!/usr/bin/env python3
"""Format conversation content as readable text.

Reads ProcessingItem JSON from stdin and outputs formatted conversation text.
"""

import json
import sys


def format_conversation(item_json: dict) -> str:
    """Format ProcessingItem content as readable text.

    Args:
        item_json: ProcessingItem dictionary.

    Returns:
        Formatted conversation text.
    """
    content_str = item_json.get("content", "")
    if not content_str:
        return "(No content)"

    try:
        content = json.loads(content_str)
    except json.JSONDecodeError as e:
        return f"(JSON parse error: {e})\n\n{content_str}"

    lines = []

    # Title
    title = content.get("name", "Untitled")
    lines.append(f"=== {title} ===")
    lines.append("")

    # Metadata
    metadata = item_json.get("metadata", {})
    created_at = metadata.get("created_at", "Unknown")
    lines.append(f"Created: {created_at}")
    lines.append("")

    # Chat messages
    chat_messages = content.get("chat_messages", [])
    if chat_messages:
        for msg in chat_messages:
            sender = msg.get("sender", "unknown")
            lines.append(f"[{sender}]")

            # Extract text from content array
            content_items = msg.get("content", [])
            if content_items:
                for item in content_items:
                    text = item.get("text", "")
                    if text:
                        lines.append(text)
            else:
                # Fallback to direct text field if content is empty
                text = msg.get("text", "")
                if text:
                    lines.append(text)

            lines.append("")
    else:
        lines.append("(No messages)")

    return "\n".join(lines)


def main():
    """Main entry point."""
    try:
        item_json = json.load(sys.stdin)
        formatted = format_conversation(item_json)
        print(formatted)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
