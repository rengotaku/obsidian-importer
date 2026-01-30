#!/usr/bin/env python3
"""
全ファイル一覧をCSV形式で出力
"""

import csv
import os
import re
import sys
from pathlib import Path

VAULTS = ['エンジニア', 'ビジネス', '経済', '日常']

def parse_frontmatter(content: str) -> dict:
    """frontmatter を解析"""
    if not content.startswith('---'):
        return {}

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}

    fm_dict = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            key, _, value = line.partition(':')
            fm_dict[key.strip()] = value.strip().strip('"\'')

    return fm_dict

def check_genre_match(filepath: Path, vault: str) -> str:
    """ジャンルが適切かチェック（簡易判定）"""
    content = filepath.read_text(encoding='utf-8')
    content_lower = content.lower()
    filename = filepath.stem.lower()

    # エンジニア向けキーワード
    tech_keywords = ['rails', 'ruby', 'python', 'javascript', 'react', 'aws', 'docker',
                     'mysql', 'postgres', 'api', 'git', 'linux', 'nginx', 'redis',
                     'activerecord', 'sql', 'html', 'css', 'node', 'golang', 'go ',
                     'terraform', 'kubernetes', 'k8s', 'ci/cd', 'jenkins', 'ansible',
                     'vim', 'vscode', 'debug', 'error', 'exception', 'code', 'プログラム',
                     'コード', '実装', 'デバッグ', 'エラー', 'クエリ', 'サーバ', 'デプロイ']

    # ビジネス向けキーワード
    biz_keywords = ['マネジメント', 'リーダー', 'ビジネス', '経営', '戦略', 'プレゼン',
                    '交渉', 'コミュニケーション', '話し方', '伝え方', '説得', '自己啓発',
                    'キャリア', '転職', '面接', '1on1', 'チーム', '組織']

    # 経済向けキーワード
    econ_keywords = ['経済', '投資', '株', '金融', '市場', 'gdp', '為替', 'インフレ',
                     '景気', '政策', '財政', '金利', '企業業績', '決算']

    # 日常向けキーワード
    daily_keywords = ['赤ちゃん', '子供', '育児', '料理', 'レシピ', '旅行', '趣味',
                      '映画', 'ゲーム', '音楽', 'スポーツ', '健康', '生活', '日常',
                      'キャラクター', 'イラスト', 'アニメ']

    def count_keywords(keywords):
        return sum(1 for kw in keywords if kw in content_lower or kw in filename)

    scores = {
        'エンジニア': count_keywords(tech_keywords),
        'ビジネス': count_keywords(biz_keywords),
        '経済': count_keywords(econ_keywords),
        '日常': count_keywords(daily_keywords)
    }

    # スコアが0なら判定不能
    if all(s == 0 for s in scores.values()):
        return '未確認'

    # 最高スコアのジャンル
    best_genre = max(scores, key=scores.get)

    if best_genre == vault:
        return 'OK'
    elif scores[vault] > 0 and scores[vault] >= scores[best_genre] * 0.5:
        return 'OK'  # 現在のジャンルもそれなりにマッチ
    else:
        return f'要確認({best_genre}?)'

def main():
    base_dir = Path(os.environ.get("OBSIDIAN_BASE_DIR", Path(__file__).resolve().parent.parent.parent))
    output_file = base_dir / '@index' / '全ファイル一覧.csv'

    rows = []

    for vault in VAULTS:
        vault_path = base_dir / vault
        if not vault_path.exists():
            continue

        for filepath in sorted(vault_path.rglob('*.md')):
            if filepath.name in ('CLAUDE.md', 'README.md'):
                continue

            try:
                content = filepath.read_text(encoding='utf-8')
                fm = parse_frontmatter(content)

                # 各フラグをチェック
                normalized = 'yes' if fm.get('normalized') == 'true' else 'no'
                reviewed = 'yes' if fm.get('reviewed') == 'true' else 'no'
                genre_match = check_genre_match(filepath, vault)

                rows.append({
                    'ファイル名': filepath.stem,
                    'vault': vault,
                    'ジャンル適合': genre_match,
                    '内容精査済み': reviewed,
                    'フォーマット済み': normalized
                })
            except Exception as e:
                rows.append({
                    'ファイル名': filepath.stem,
                    'vault': vault,
                    'ジャンル適合': 'エラー',
                    '内容精査済み': 'エラー',
                    'フォーマット済み': 'エラー'
                })

    # CSV出力
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ファイル名', 'vault', 'ジャンル適合', '内容精査済み', 'フォーマット済み'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"出力完了: {output_file}")
    print(f"総件数: {len(rows)}")

    # サマリ
    print("\n=== サマリ ===")
    for vault in VAULTS:
        vault_rows = [r for r in rows if r['vault'] == vault]
        ok_count = sum(1 for r in vault_rows if r['ジャンル適合'] == 'OK')
        review_needed = sum(1 for r in vault_rows if '要確認' in r['ジャンル適合'])
        print(f"{vault}: {len(vault_rows)}件 (適合:{ok_count}, 要確認:{review_needed})")

if __name__ == '__main__':
    main()
