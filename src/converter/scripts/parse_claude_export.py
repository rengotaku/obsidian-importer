#!/usr/bin/env python3
"""
Claude Export Data Parser
エクスポートされた Claude データを Obsidian ノートに変換する

Usage:
    python parse_claude_export.py <export_dir> [--output <output_dir>]

Example:
    python parse_claude_export.py @index/claude/claude-data-2026-01-08-01-09-46-batch-0000
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
import re


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """ファイル名として安全な文字列に変換"""
    # 不正な文字を置換
    invalid_chars = r'[<>:"/\\|?*\n\r\t]'
    safe = re.sub(invalid_chars, '_', name)
    # 連続するアンダースコアを1つに
    safe = re.sub(r'_+', '_', safe)
    # 前後の空白とアンダースコアを除去
    safe = safe.strip(' _')
    # 長さ制限
    if len(safe) > max_length:
        safe = safe[:max_length].rsplit('_', 1)[0]
    return safe or 'untitled'


def format_datetime(dt_str: str) -> str:
    """ISO形式の日時を読みやすい形式に変換"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_str


def generate_title_from_messages(messages: list, max_length: int = 50) -> str:
    """メッセージからタイトルを生成"""
    for msg in messages:
        if msg.get('sender') == 'human':
            text = msg.get('text', '').strip()
            if text:
                # 最初の行を取得
                first_line = text.split('\n')[0].strip()
                if len(first_line) > max_length:
                    first_line = first_line[:max_length].rsplit(' ', 1)[0] + '...'
                return first_line
    return 'Untitled Conversation'


def parse_conversations(data: list, output_dir: Path) -> dict:
    """会話データを解析してMarkdownに変換"""
    conversations_dir = output_dir / 'conversations'
    conversations_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': len(data),
        'by_month': {},
        'conversations': []
    }

    for conv in data:
        uuid = conv.get('uuid', 'unknown')
        name = conv.get('name', '').strip()
        summary = conv.get('summary', '')
        created_at = conv.get('created_at', '')
        updated_at = conv.get('updated_at', '')
        messages = conv.get('chat_messages', [])

        # タイトルが空の場合、最初のメッセージから生成
        if not name:
            name = generate_title_from_messages(messages)

        # 月別統計
        try:
            month = created_at[:7]  # YYYY-MM
            stats['by_month'][month] = stats['by_month'].get(month, 0) + 1
        except:
            pass

        # ファイル名生成
        date_prefix = created_at[:10] if created_at else ''
        filename = sanitize_filename(f"{date_prefix}_{name}")
        filepath = conversations_dir / f"{filename}.md"

        # 重複回避
        counter = 1
        while filepath.exists():
            filepath = conversations_dir / f"{filename}_{counter}.md"
            counter += 1

        # Markdown生成
        content = generate_conversation_md(
            name=name,
            uuid=uuid,
            summary=summary,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages
        )

        filepath.write_text(content, encoding='utf-8')

        stats['conversations'].append({
            'name': name,
            'uuid': uuid,
            'file': filepath.name,
            'created': created_at,
            'message_count': len(messages)
        })

    return stats


def generate_conversation_md(name: str, uuid: str, summary: str,
                            created_at: str, updated_at: str,
                            messages: list) -> str:
    """会話のMarkdownを生成"""

    # タグ推測
    tags = ['claude-export', 'conversation']
    name_lower = name.lower()
    if any(w in name_lower for w in ['code', 'プログラ', '開発', 'dev', 'api']):
        tags.append('tech')
    if any(w in name_lower for w in ['setup', 'セットアップ', 'インストール', 'config']):
        tags.append('setup')

    md = f"""---
title: "{name}"
uuid: {uuid}
created: {created_at[:10] if created_at else ''}
updated: {updated_at[:10] if updated_at else ''}
tags:
{chr(10).join(f'  - {tag}' for tag in tags)}
message_count: {len(messages)}
---

# {name}

"""

    # サマリー
    if summary:
        md += f"""## Summary

{summary}

"""

    # メッセージ
    if messages:
        md += "## Conversation\n\n"
        for msg in messages:
            sender = msg.get('sender', 'unknown')
            text = msg.get('text', '')
            timestamp = msg.get('created_at', '')

            icon = '👤' if sender == 'human' else '🤖'
            time_str = format_datetime(timestamp) if timestamp else ''

            md += f"### {icon} {sender.capitalize()}"
            if time_str:
                md += f" ({time_str})"
            md += "\n\n"

            # テキストを適切にフォーマット
            if text:
                # コードブロックの保持
                md += text + "\n\n"

    return md


def parse_memories(data: list, output_dir: Path) -> None:
    """メモリーデータを解析"""
    if not data:
        return

    memories_file = output_dir / 'Claude_Memories.md'

    memory_data = data[0] if data else {}
    conv_memory = memory_data.get('conversations_memory', '')
    project_memories = memory_data.get('project_memories', {})

    md = """---
title: Claude Memories
tags:
  - claude-export
  - memory
  - context
---

# Claude Memories

Claudeが記憶しているユーザーコンテキスト。

## Conversation Memory

"""
    md += conv_memory + "\n\n"

    if project_memories:
        md += "## Project Memories\n\n"
        for proj_uuid, memory in project_memories.items():
            md += f"### Project: {proj_uuid[:8]}...\n\n"
            md += memory + "\n\n---\n\n"

    memories_file.write_text(md, encoding='utf-8')


def parse_projects(data: list, output_dir: Path) -> None:
    """プロジェクトデータを解析"""
    if not data:
        return

    projects_file = output_dir / 'Claude_Projects.md'

    md = """---
title: Claude Projects
tags:
  - claude-export
  - projects
---

# Claude Projects

Claude.ai で作成したプロジェクト一覧。

| Project | Created | Description |
|---------|---------|-------------|
"""

    for proj in data:
        name = proj.get('name', 'Untitled')
        created = proj.get('created_at', '')[:10]
        desc = proj.get('description', '').replace('\n', ' ')[:50]
        md += f"| {name} | {created} | {desc}... |\n"

    md += "\n---\n\n## Project Details\n\n"

    for proj in data:
        name = proj.get('name', 'Untitled')
        uuid = proj.get('uuid', '')
        desc = proj.get('description', '')
        template = proj.get('prompt_template', '')
        created = proj.get('created_at', '')

        md += f"""### {name}

- **UUID**: `{uuid}`
- **Created**: {created[:10] if created else 'N/A'}

"""
        if desc:
            md += f"**Description:**\n\n{desc}\n\n"
        if template:
            md += f"**Prompt Template:**\n\n```\n{template}\n```\n\n"
        md += "---\n\n"

    projects_file.write_text(md, encoding='utf-8')


def generate_index(stats: dict, output_dir: Path) -> None:
    """インデックスファイルを生成"""
    index_file = output_dir / 'Claude_Export_Index.md'

    md = f"""---
title: Claude Export Index
tags:
  - claude-export
  - index
created: {datetime.now().strftime('%Y-%m-%d')}
---

# Claude Export Index

エクスポートされた Claude データの概要。

## Statistics

- **Total Conversations**: {stats['total']}
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## By Month

| Month | Count |
|-------|-------|
"""

    for month in sorted(stats['by_month'].keys(), reverse=True):
        count = stats['by_month'][month]
        md += f"| {month} | {count} |\n"

    md += """
## Files

- [[Claude_Memories]] - Claudeが記憶しているコンテキスト
- [[Claude_Projects]] - プロジェクト一覧

## Recent Conversations

"""

    # 最新10件
    recent = sorted(stats['conversations'],
                   key=lambda x: x['created'],
                   reverse=True)[:10]

    for conv in recent:
        name = conv['name']
        file = conv['file'].replace('.md', '')
        created = conv['created'][:10] if conv['created'] else ''
        msgs = conv['message_count']
        md += f"- [[{file}|{name}]] ({created}, {msgs} messages)\n"

    index_file.write_text(md, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Parse Claude export data')
    parser.add_argument('export_dir', help='Path to Claude export directory')
    parser.add_argument('--output', '-o',
                       default=None,
                       help='Output directory (default: same as export_dir)')
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    output_dir = Path(args.output) if args.output else export_dir / 'parsed'

    if not export_dir.exists():
        print(f"Error: Directory not found: {export_dir}")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing Claude export from: {export_dir}")
    print(f"Output directory: {output_dir}")

    # conversations.json
    conv_file = export_dir / 'conversations.json'
    if conv_file.exists():
        print("Parsing conversations...")
        with open(conv_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stats = parse_conversations(data, output_dir)
        print(f"  -> {stats['total']} conversations parsed")
    else:
        stats = {'total': 0, 'by_month': {}, 'conversations': []}

    # memories.json
    mem_file = export_dir / 'memories.json'
    if mem_file.exists():
        print("Parsing memories...")
        with open(mem_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        parse_memories(data, output_dir)
        print("  -> Memories parsed")

    # projects.json
    proj_file = export_dir / 'projects.json'
    if proj_file.exists():
        print("Parsing projects...")
        with open(proj_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        parse_projects(data, output_dir)
        print("  -> Projects parsed")

    # Index
    print("Generating index...")
    generate_index(stats, output_dir)

    print(f"\nDone! Output written to: {output_dir}")
    return 0


if __name__ == '__main__':
    exit(main())
