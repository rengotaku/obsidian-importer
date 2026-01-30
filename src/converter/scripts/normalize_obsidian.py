#!/usr/bin/env python3
"""
Obsidian ファイル正規化スクリプト
- ファイル名をタイトルのみに変更
- frontmatter に normalized: true を追加
- Jekyll特有フィールドを削除
- created フィールドを追加（ファイル名から抽出）
"""

import json
import os
import re
import sys
from pathlib import Path

JEKYLL_FIELDS = {'draft', 'private', 'slug', 'lastmod', 'keywords', 'headless'}
DATE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})-(.+)$')
INLINE_ARRAY_PATTERN = re.compile(r'^\[.*\]$')

def extract_date_and_title(filename: str) -> tuple[str | None, str]:
    """ファイル名から日付とタイトルを抽出"""
    stem = Path(filename).stem
    match = DATE_PATTERN.match(stem)
    if match:
        date = match.group(1)
        title = match.group(2).replace('-', ' ').replace('_', ' ')
        return date, title
    return None, stem

def parse_inline_array(value: str) -> list:
    """インライン配列 ["a", "b"] をパース"""
    value = value.strip()
    if INLINE_ARRAY_PATTERN.match(value):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # JSON パースに失敗したら文字列として返す
            pass
    return value

def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """frontmatter を解析して辞書と本文を返す"""
    if not content.startswith('---'):
        return None, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content

    fm_lines = parts[1].strip().split('\n')
    fm_dict = {}
    current_key = None
    current_list = None

    for line in fm_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # リスト項目 (インデントされた - item)
        if (line.startswith('  - ') or line.startswith('\t- ') or
            (line.startswith('  ') and stripped.startswith('- '))):
            if current_key and current_list is not None:
                item = stripped[2:].strip().strip('"\'')
                current_list.append(item)
            continue

        # キー: 値
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            # 前のリストを保存
            if current_key and current_list is not None:
                fm_dict[current_key] = current_list
                current_key = None
                current_list = None

            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()

            # 値がない場合はリストの開始
            if not value:
                current_key = key
                current_list = []
            else:
                # クォートを除去
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # インライン配列をパース
                parsed = parse_inline_array(value)
                fm_dict[key] = parsed

    # 最後のリストを保存
    if current_key and current_list is not None:
        fm_dict[current_key] = current_list

    body = parts[2]
    return fm_dict, body

def build_frontmatter(fm_dict: dict) -> str:
    """辞書から frontmatter 文字列を生成"""
    lines = ['---']

    # 順序を指定
    order = ['title', 'normalized', 'created', 'tags', 'related']

    def format_value(key, value):
        if isinstance(value, list):
            if not value:
                return []
            result = [f'{key}:']
            for item in value:
                item_str = str(item)
                if '[[' in item_str or ' ' in item_str or ':' in item_str:
                    result.append(f'  - "{item_str}"')
                else:
                    result.append(f'  - {item_str}')
            return result
        elif isinstance(value, bool):
            return [f'{key}: {str(value).lower()}']
        elif value == 'true' or value == 'false':
            return [f'{key}: {value}']
        else:
            value_str = str(value)
            if ' ' in value_str or ':' in value_str:
                return [f'{key}: "{value_str}"']
            else:
                return [f'{key}: {value_str}']

    # 指定順で出力
    for key in order:
        if key in fm_dict and fm_dict[key]:
            lines.extend(format_value(key, fm_dict[key]))

    # 残りのキー (Jekyll フィールド以外)
    for key, value in fm_dict.items():
        if key not in order and key not in JEKYLL_FIELDS and value:
            lines.extend(format_value(key, value))

    lines.append('---')
    return '\n'.join(lines)

def normalize_file(filepath: Path, dry_run: bool = False) -> tuple[bool, Path | None]:
    """ファイルを正規化。(変更有無, 新ファイルパス) を返す"""
    content = filepath.read_text(encoding='utf-8')

    fm_dict, body = parse_frontmatter(content)

    if fm_dict is None:
        fm_dict = {}

    # ファイル名から日付とタイトルを抽出
    date_from_filename, title_from_filename = extract_date_and_title(filepath.name)

    # タイトル決定: frontmatter > ファイル名から生成
    if 'title' not in fm_dict or not fm_dict['title']:
        fm_dict['title'] = title_from_filename

    # created 決定: frontmatter の date > created > ファイル名から抽出
    if 'created' not in fm_dict:
        if 'date' in fm_dict:
            # Jekyll の date フィールドから抽出 (2018-04-20T11:01:20+09:00 形式)
            date_str = str(fm_dict['date'])
            if 'T' in date_str:
                fm_dict['created'] = date_str.split('T')[0]
            else:
                fm_dict['created'] = date_str[:10]
        elif date_from_filename:
            fm_dict['created'] = date_from_filename

    # date フィールドを削除 (created に移行済み)
    fm_dict.pop('date', None)

    # normalized フラグ追加
    fm_dict['normalized'] = True

    # Jekyll特有フィールドを削除
    for field in JEKYLL_FIELDS:
        fm_dict.pop(field, None)

    # 新しい内容を生成
    new_content = build_frontmatter(fm_dict) + '\n' + body.lstrip('\n')

    # 新しいファイル名を決定
    title = str(fm_dict['title'])
    new_filename = title + '.md'
    # ファイル名に使えない文字を置換
    new_filename = re.sub(r'[<>:"/\\|?*]', '_', new_filename)
    new_filepath = filepath.parent / new_filename

    if dry_run:
        print(f"[DRY-RUN] {filepath.name} -> {new_filename}")
        return True, new_filepath

    # ファイル名が変わる場合
    if filepath.name != new_filename:
        # 同名ファイルが既に存在する場合は番号を付ける
        if new_filepath.exists():
            base = new_filepath.stem
            i = 2
            while new_filepath.exists():
                new_filepath = filepath.parent / f"{base} ({i}).md"
                i += 1

        # 先に内容を書き込んでからリネーム
        filepath.write_text(new_content, encoding='utf-8')
        filepath.rename(new_filepath)
    else:
        filepath.write_text(new_content, encoding='utf-8')

    return True, new_filepath

def main():
    if len(sys.argv) < 2:
        print("Usage: normalize_obsidian.py <directory> [--dry-run]")
        sys.exit(1)

    target_dir = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not target_dir.is_dir():
        print(f"Error: {target_dir} is not a directory")
        sys.exit(1)

    count = 0
    errors = []

    # ファイルリストを先に取得（リネーム中の影響を避ける）
    files = list(target_dir.rglob('*.md'))

    for filepath in files:
        # CLAUDE.md や README.md はスキップ
        if filepath.name in ('CLAUDE.md', 'README.md'):
            continue

        try:
            changed, new_path = normalize_file(filepath, dry_run)
            if changed:
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} files...")
        except Exception as e:
            errors.append(f"{filepath}: {e}")

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Normalized {count} files in {target_dir}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

if __name__ == '__main__':
    main()
