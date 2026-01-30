#!/usr/bin/env python3
"""
Claude Export Importer
Claude エクスポートデータを解析し、Obsidian ノートとして適切な Vault に振り分ける

Usage:
    python import_claude_conversations.py <export_dir> [--dry-run]
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
import re
from typing import Tuple


# 分類キーワード
CLASSIFICATION_RULES = {
    'Engineering': {
        'keywords': [
            # プログラミング言語
            'python', 'javascript', 'typescript', 'ruby', 'go', 'rust', 'java',
            'rails', 'react', 'vue', 'node', 'docker', 'kubernetes', 'k8s',
            # 技術用語
            'api', 'database', 'sql', 'git', 'github', 'cli', 'terminal',
            'server', 'nginx', 'linux', 'ubuntu', 'systemd', 'ssh',
            'code', 'function', 'class', 'debug', 'error', 'bug',
            'deploy', 'ci/cd', 'devops', 'aws', 'cloud',
            # 日本語キーワード
            'プログラ', '開発', 'コード', 'サーバー', 'データベース',
            'インストール', 'セットアップ', '設定', 'エラー', 'バグ',
            'コマンド', 'ターミナル', '実装', 'テスト',
        ],
        'weight': 1.0,
    },
    'ビジネス書': {
        'keywords': [
            # ビジネススキル
            'ビジネス', 'マネジメント', 'リーダーシップ', '経営',
            'プレゼン', '交渉', 'コミュニケーション', '話し方',
            '会議', 'ファシリテ', 'キャリア', '転職', '就職',
            '自己啓発', '習慣', '生産性', '時間管理',
            # 書籍関連
            '本', '書籍', '読書', '要約', 'サマリ',
            'management', 'leadership', 'career', 'productivity',
        ],
        'weight': 1.0,
    },
    '経済': {
        'keywords': [
            # 経済・金融
            '経済', '金融', '投資', '株', '為替', '円安', '円高',
            'nisa', 'ideco', '資産', '運用', '配当', '利回り',
            '市場', 'マーケット', '景気', 'gdp', 'インフレ',
            # 企業・業界
            '決算', '業績', '企業', '会社', 'ipo', 'm&a',
            # 政策
            '政策', '規制', '金利', '日銀', 'fed',
            'economy', 'finance', 'investment', 'market',
        ],
        'weight': 1.0,
    },
}


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """ファイル名として安全な文字列に変換"""
    invalid_chars = r'[<>:"/\\|?*\n\r\t]'
    safe = re.sub(invalid_chars, '_', name)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip(' _')
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


def classify_conversation(name: str, summary: str, messages: list) -> Tuple[str, float]:
    """会話の内容からジャンルを分類"""
    # テキストを結合
    text_parts = [name.lower(), summary.lower()]
    for msg in messages[:5]:  # 最初の5メッセージを使用
        text_parts.append(msg.get('text', '').lower())
    full_text = ' '.join(text_parts)

    scores = {}
    for category, rules in CLASSIFICATION_RULES.items():
        score = 0
        for keyword in rules['keywords']:
            if keyword.lower() in full_text:
                score += 1
        scores[category] = score * rules['weight']

    if not scores or max(scores.values()) == 0:
        return ('未分類', 0.0)

    best_category = max(scores, key=scores.get)
    confidence = scores[best_category] / (sum(scores.values()) + 1)

    return (best_category, confidence)


def generate_title_from_messages(messages: list, max_length: int = 50) -> str:
    """メッセージからタイトルを生成"""
    for msg in messages:
        if msg.get('sender') == 'human':
            text = msg.get('text', '').strip()
            if text:
                first_line = text.split('\n')[0].strip()
                if len(first_line) > max_length:
                    first_line = first_line[:max_length].rsplit(' ', 1)[0] + '...'
                return first_line
    return 'Untitled Conversation'


def generate_conversation_md(name: str, uuid: str, summary: str,
                            created_at: str, updated_at: str,
                            messages: list, category: str) -> str:
    """会話のMarkdownを生成"""
    tags = ['claude-export', 'conversation', category.lower().replace('書', '')]

    md = f"""---
title: "{name}"
uuid: {uuid}
created: {created_at[:10] if created_at else ''}
updated: {updated_at[:10] if updated_at else ''}
category: {category}
tags:
{chr(10).join(f'  - {tag}' for tag in tags)}
message_count: {len(messages)}
---

# {name}

"""

    if summary:
        md += f"""> [!summary] Summary
> {summary[:500]}{'...' if len(summary) > 500 else ''}

"""

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

            if text:
                md += text + "\n\n"

    return md


def process_conversations(data: list, base_dir: Path, dry_run: bool = False) -> dict:
    """会話データを処理して適切なVaultに振り分け"""
    stats = {
        'total': len(data),
        'by_category': {},
        'conversations': [],
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

        # 分類
        category, confidence = classify_conversation(name, summary, messages)

        # 統計更新
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

        # 出力先決定
        if category == '未分類':
            output_dir = base_dir / '@index' / 'claude' / 'uncategorized'
        else:
            output_dir = base_dir / category / 'claude-conversations'

        # ファイル名生成
        date_prefix = created_at[:10] if created_at else ''
        filename = sanitize_filename(f"{date_prefix}_{name}")
        filepath = output_dir / f"{filename}.md"

        # 重複回避
        counter = 1
        base_filepath = filepath
        while filepath.exists():
            filepath = output_dir / f"{filename}_{counter}.md"
            counter += 1

        # Markdown生成
        content = generate_conversation_md(
            name=name,
            uuid=uuid,
            summary=summary,
            created_at=created_at,
            updated_at=updated_at,
            messages=messages,
            category=category
        )

        stats['conversations'].append({
            'name': name,
            'uuid': uuid,
            'category': category,
            'confidence': confidence,
            'file': str(filepath.relative_to(base_dir)),
            'created': created_at,
        })

        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding='utf-8')

    return stats


def generate_import_report(stats: dict, base_dir: Path, dry_run: bool = False) -> str:
    """インポートレポートを生成"""
    report = f"""---
title: Claude Import Report
created: {datetime.now().strftime('%Y-%m-%d')}
tags:
  - claude-export
  - report
---

# Claude Import Report

{'**DRY RUN** - 実際のファイルは作成されていません' if dry_run else ''}

## Statistics

- **Total Conversations**: {stats['total']}
- **Import Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## By Category

| Category | Count |
|----------|-------|
"""
    for cat in sorted(stats['by_category'].keys()):
        count = stats['by_category'][cat]
        report += f"| {cat} | {count} |\n"

    report += "\n## Recent Imports\n\n"
    recent = sorted(stats['conversations'], key=lambda x: x['created'], reverse=True)[:20]
    for conv in recent:
        report += f"- **{conv['category']}**: {conv['name']} → `{conv['file']}`\n"

    return report


def main():
    parser = argparse.ArgumentParser(description='Import Claude export data to Obsidian vaults')
    parser.add_argument('export_dir', help='Path to Claude export directory')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--base-dir', '-b', default=None,
                       help='Base directory for Obsidian vaults (default: parent of export_dir)')
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        # デフォルト: export_dir の親の親（@index/claude/xxx → Obsidian/）
        base_dir = export_dir.parent.parent.parent

    if not export_dir.exists():
        print(f"Error: Directory not found: {export_dir}")
        return 1

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Importing Claude export from: {export_dir}")
    print(f"Base directory: {base_dir}")

    # conversations.json
    conv_file = export_dir / 'conversations.json'
    if not conv_file.exists():
        print(f"Error: conversations.json not found in {export_dir}")
        return 1

    print("Loading conversations...")
    with open(conv_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} conversations...")
    stats = process_conversations(data, base_dir, dry_run=args.dry_run)

    # レポート出力
    print("\n=== Import Summary ===")
    for cat in sorted(stats['by_category'].keys()):
        count = stats['by_category'][cat]
        print(f"  {cat}: {count}")

    # レポートファイル保存
    report = generate_import_report(stats, base_dir, dry_run=args.dry_run)
    report_file = base_dir / '@index' / 'claude' / 'import_report.md'
    if not args.dry_run:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {report_file}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done!")
    return 0


if __name__ == '__main__':
    exit(main())
