#!/usr/bin/env python3
"""
Tag Extractor - 既存VaultからタグをFR-004に基づいて抽出・カテゴリ分類

Usage:
    python3 tag_extractor.py [options]

Options:
    --output, -o    出力先ファイルパス（デフォルト: .claude/scripts/data/tag_dictionary.json）
    --limit         各カテゴリの最大タグ数（デフォルト: 30）
    --vaults        対象Vault（カンマ区切り、デフォルト: 全Vault）
    --json          JSON形式で出力
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TypedDict


# =============================================================================
# Configuration
# =============================================================================

OBSIDIAN_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = OBSIDIAN_ROOT / "scripts/data/tag_dictionary.json"
DEFAULT_LIMIT = 30

# Vault directories to scan
VAULT_DIRS = ["エンジニア", "ビジネス", "経済", "日常", "その他"]

# Tag categorization keywords
CATEGORY_KEYWORDS = {
    "languages": [
        "python", "ruby", "rails", "golang", "go", "javascript", "typescript",
        "java", "kotlin", "swift", "rust", "c", "cpp", "csharp", "php",
        "scala", "elixir", "haskell", "clojure", "lua", "perl", "r",
        "nodejs", "react", "vue", "angular", "django", "flask", "spring",
        "nextjs", "nuxt", "svelte", "express", "fastapi", "gin"
    ],
    "infrastructure": [
        "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "linux",
        "nginx", "apache", "terraform", "ansible", "jenkins", "circleci",
        "github-actions", "gitlab-ci", "prometheus", "grafana", "elasticsearch",
        "redis", "postgresql", "mysql", "mongodb", "dynamodb", "s3",
        "ec2", "lambda", "ecs", "eks", "cloudflare", "vercel", "netlify"
    ],
    "tools": [
        "git", "bash", "vim", "neovim", "emacs", "vscode", "ssh", "tmux",
        "make", "cmake", "webpack", "vite", "npm", "yarn", "pnpm",
        "pip", "poetry", "cargo", "homebrew", "apt", "yum"
    ],
    "concepts": [
        "api", "rest", "graphql", "grpc", "security", "authentication",
        "authorization", "oauth", "jwt", "ssl", "tls", "encryption",
        "testing", "tdd", "ci", "cd", "devops", "agile", "scrum",
        "microservices", "monolith", "architecture", "design-pattern",
        "performance", "optimization", "caching", "logging", "monitoring"
    ],
    "lifestyle": [
        "旅行", "料理", "健康", "運動", "趣味", "読書", "映画", "音楽",
        "ゲーム", "写真", "アート", "デザイン", "ファッション", "美容",
        "話し方", "コミュニケーション", "習慣", "生活", "家事"
    ]
}

# Tags to exclude (auto-generated or not useful)
EXCLUDE_TAGS = {
    "conversation", "claude-export", "draft", "wip", "todo",
    "未整理", "要確認", "imported"
}


# =============================================================================
# Type Definitions
# =============================================================================

class TagDictionary(TypedDict):
    languages: list[str]
    infrastructure: list[str]
    tools: list[str]
    concepts: list[str]
    lifestyle: list[str]
    total_count: int
    extracted_at: str
    source_vaults: list[str]


# =============================================================================
# Core Functions
# =============================================================================

def normalize_tag(tag: str) -> str:
    """タグを正規化（小文字化、ハイフン統一）"""
    # 小文字化
    tag = tag.lower().strip()
    # スペースをハイフンに
    tag = tag.replace(" ", "-")
    # 連続ハイフンを単一に
    tag = re.sub(r"-+", "-", tag)
    # 先頭末尾のハイフン除去
    tag = tag.strip("-")
    return tag


def extract_frontmatter_tags(content: str) -> list[str]:
    """Markdownファイルからfrontmatterのtagsを抽出"""
    # YAML frontmatter抽出
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return []

    frontmatter = match.group(1)
    tags = []

    # tags: フィールドを検索
    # パターン1: tags: [tag1, tag2, tag3]
    inline_match = re.search(r"tags:\s*\[(.*?)\]", frontmatter)
    if inline_match:
        tag_str = inline_match.group(1)
        tags = [t.strip().strip("'\"") for t in tag_str.split(",")]
    else:
        # パターン2: tags:\n  - tag1\n  - tag2
        in_tags_block = False
        for line in frontmatter.split("\n"):
            if line.startswith("tags:"):
                in_tags_block = True
                # 同一行にタグがある場合
                remaining = line[5:].strip()
                if remaining and not remaining.startswith("-"):
                    tags.append(remaining.strip("'\""))
            elif in_tags_block:
                if line.strip().startswith("-"):
                    tag = line.strip().lstrip("-").strip().strip("'\"")
                    if tag:
                        tags.append(tag)
                elif line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    # 別のフィールドに到達
                    break

    return [normalize_tag(t) for t in tags if t]


def categorize_tag(tag: str) -> str | None:
    """タグをカテゴリに分類"""
    tag_lower = tag.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if tag_lower in keywords:
            return category
        # 部分一致も許容（例: "rails" in "ruby-on-rails"）
        for keyword in keywords:
            if keyword in tag_lower or tag_lower in keyword:
                return category

    # カテゴリ不明の場合
    # 日本語を含む場合はlifestyle候補
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", tag):
        return "lifestyle"

    # 英語のみならconcepts候補
    return "concepts"


def scan_vault(vault_path: Path) -> Counter:
    """Vaultディレクトリをスキャンしてタグを収集"""
    tag_counter: Counter = Counter()

    if not vault_path.exists():
        return tag_counter

    for md_file in vault_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            tags = extract_frontmatter_tags(content)
            for tag in tags:
                if tag and tag not in EXCLUDE_TAGS:
                    tag_counter[tag] += 1
        except (UnicodeDecodeError, OSError):
            continue

    return tag_counter


def extract_tag_dictionary(
    vaults: list[str] | None = None,
    limit: int = DEFAULT_LIMIT
) -> TagDictionary:
    """Vaultからタグ辞書を抽出"""
    if vaults is None:
        vaults = VAULT_DIRS

    # 全タグを収集
    all_tags: Counter = Counter()
    for vault_name in vaults:
        vault_path = OBSIDIAN_ROOT / vault_name
        vault_tags = scan_vault(vault_path)
        all_tags.update(vault_tags)

    # カテゴリ別に分類
    categorized: dict[str, Counter] = {
        "languages": Counter(),
        "infrastructure": Counter(),
        "tools": Counter(),
        "concepts": Counter(),
        "lifestyle": Counter()
    }

    for tag, count in all_tags.items():
        category = categorize_tag(tag)
        if category:
            categorized[category][tag] = count

    # 各カテゴリから頻度上位を抽出
    result: TagDictionary = {
        "languages": [t for t, _ in categorized["languages"].most_common(limit)],
        "infrastructure": [t for t, _ in categorized["infrastructure"].most_common(limit)],
        "tools": [t for t, _ in categorized["tools"].most_common(limit)],
        "concepts": [t for t, _ in categorized["concepts"].most_common(limit)],
        "lifestyle": [t for t, _ in categorized["lifestyle"].most_common(limit)],
        "total_count": sum(len(v) for v in categorized.values()),
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "source_vaults": vaults
    }

    return result


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="既存Vaultからタグ辞書を抽出"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"出力先ファイルパス（デフォルト: {DEFAULT_OUTPUT}）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"各カテゴリの最大タグ数（デフォルト: {DEFAULT_LIMIT}）"
    )
    parser.add_argument(
        "--vaults",
        type=str,
        default=None,
        help="対象Vault（カンマ区切り、デフォルト: 全Vault）"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で標準出力"
    )

    args = parser.parse_args()

    # Vault指定のパース
    vaults = None
    if args.vaults:
        vaults = [v.strip() for v in args.vaults.split(",")]

    # 抽出実行
    result = extract_tag_dictionary(vaults=vaults, limit=args.limit)

    # 出力
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 人間可読形式
        print("📊 タグ辞書抽出完了")
        print(f"  言語: {len(result['languages'])} タグ ({', '.join(result['languages'][:5])}...)")
        print(f"  インフラ: {len(result['infrastructure'])} タグ ({', '.join(result['infrastructure'][:5])}...)")
        print(f"  ツール: {len(result['tools'])} タグ ({', '.join(result['tools'][:5])}...)")
        print(f"  概念: {len(result['concepts'])} タグ ({', '.join(result['concepts'][:5])}...)")
        print(f"  日常: {len(result['lifestyle'])} タグ ({', '.join(result['lifestyle'][:5])}...)")
        print("  ─────────────────")
        print(f"  合計: {result['total_count']} タグ")

        # ファイル出力
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  出力: {args.output}")


if __name__ == "__main__":
    main()
