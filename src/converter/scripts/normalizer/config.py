"""
Configuration - 設定値、定数、パス定義

このモジュールは他のモジュールから依存されるため、
インポートサイクルを避けるために他のnormalizerモジュールをインポートしない。
"""
from __future__ import annotations

import os
from pathlib import Path

# =============================================================================
# Base Paths
# =============================================================================

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")
BASE_DIR = Path(os.environ.get("OBSIDIAN_BASE_DIR", Path(__file__).resolve().parent.parent.parent.parent))

# NORMALIZER_INDEX_DIR 環境変数でテスト用ディレクトリを切り替え可能
_index_dir_override = os.environ.get("NORMALIZER_INDEX_DIR")
# 標準のステージングパス: .staging/@index/
STAGING_DIR = BASE_DIR / ".staging"
INDEX_DIR = Path(_index_dir_override) if _index_dir_override else STAGING_DIR / "@index"
DUST_DIR = STAGING_DIR / "@dust"
SESSION_DIR = STAGING_DIR / "@session"

# =============================================================================
# Genre Definitions (動的取得)
# =============================================================================

VAULTS_DIR = BASE_DIR / "Vaults"

# 自動振り分け対象外のフォルダ（CLAUDE.md参照: 手動管理）
EXCLUDED_VAULTS = {"ClaudedocKnowledges"}


def _scan_vaults() -> tuple[list[str], dict[str, Path]]:
    """Vaults/ フォルダをスキャンしてジャンルリストとVAULT_MAPを構築

    Returns:
        tuple: (genres_list, vault_map)
    """
    genres: list[str] = []
    vault_map: dict[str, Path] = {}

    if VAULTS_DIR.exists():
        for item in sorted(VAULTS_DIR.iterdir()):
            # 隠しフォルダと除外フォルダをスキップ
            if item.is_dir() and not item.name.startswith(".") and item.name not in EXCLUDED_VAULTS:
                genres.append(item.name)
                vault_map[item.name] = item

    # dust は特別: @dust フォルダへ
    genres.append("dust")
    vault_map["dust"] = DUST_DIR

    return genres, vault_map


# モジュール読み込み時にスキャン実行
GENRES, VAULT_MAP = _scan_vaults()

# ジャンル説明（プロンプト用）- 既知のジャンルの説明
# 新規フォルダは説明なしでフォルダ名のみ使用
GENRE_DESCRIPTIONS: dict[str, str] = {
    "エンジニア": "プログラミング、技術文書、システム設計、DevOps、AI/ML、インフラ",
    "ビジネス": "ビジネス書要約、マネジメント、キャリア、コミュニケーション、自己啓発",
    "経済": "経済ニュース、投資、市場分析、金融、企業分析",
    "日常": "日常生活、趣味、雑記、旅行、健康",
    "その他": "上記に該当しないが価値のあるコンテンツ",
    "dust": "価値なし（テスト投稿、意味不明、空内容、ゴミデータ）",
}


def get_genre_definitions_text() -> str:
    """プロンプト用のジャンル定義テキストを生成

    Returns:
        ジャンル定義テキスト（Markdown形式）
    """
    lines = []
    for i, genre in enumerate(GENRES, 1):
        desc = GENRE_DESCRIPTIONS.get(genre, f"{genre} に関するコンテンツ")
        lines.append(f"{i}. **{genre}**: {desc}")
    return "\n".join(lines)

# =============================================================================
# Processing Settings
# =============================================================================

MAX_CONTENT_CHARS = 4000
API_TIMEOUT = 120
API_DELAY = 0.3

# =============================================================================
# Prompt Settings
# =============================================================================

# スクリプトは .dev/scripts/ 配下にある
DEV_DIR = BASE_DIR / ".dev"
PROMPTS_DIR = DEV_DIR / "scripts/prompts"
PROMPT_TEMPLATE_PATH = PROMPTS_DIR / "normalizer_v2.txt"
EXAMPLES_DIR = PROMPTS_DIR / "examples"
TAG_DICTIONARY_PATH = DEV_DIR / "scripts/data/tag_dictionary.json"

# Stage prompt file mapping (旧形式 - Phase 5で削除予定)
STAGE_PROMPTS = {
    "stage1_dust": PROMPTS_DIR / "stage1_dust.txt",
    "stage2_genre": PROMPTS_DIR / "stage2_genre.txt",
    "stage3_normalize": PROMPTS_DIR / "stage3_normalize.txt",
    "stage4_metadata": PROMPTS_DIR / "stage4_metadata.txt",
    "stage5_summary": PROMPTS_DIR / "stage5_summary.txt",
}

# New stage prompt file mapping (Pipeline統合用)
NEW_STAGE_PROMPTS = {
    "stage_a_classify": PROMPTS_DIR / "stage_a_classify.txt",
    "stage_b_normalize": PROMPTS_DIR / "stage3_normalize.txt",  # 既存を再利用
    "stage_c_metadata": PROMPTS_DIR / "stage_c_metadata.txt",
}

# =============================================================================
# System Prompt
# =============================================================================


def get_normalizer_system_prompt() -> str:
    """動的にシステムプロンプトを生成

    Returns:
        システムプロンプト文字列
    """
    genre_defs = get_genre_definitions_text()
    # f-string内のJSONの中括弧はダブルエスケープ
    return f"""あなたはObsidianナレッジベースの整理AIです。
ファイルの内容を分析し、適切なジャンル分類と正規化を行ってください。

## ジャンル定義

{genre_defs}

## dust判定基準
- 内容が極端に短い（実質的な情報なし）
- テスト投稿や意味のない文字列
- 重複・コピーミスと思われるもの
- 破損して読解不能なもの

## 出力形式
必ず以下のJSON形式のみで回答してください。説明文は不要です。

```json
{{
  "genre": "ジャンル名",
  "confidence": 0.0-1.0,
  "is_dust": false,
  "dust_reason": null,
  "related_keywords": ["キーワード1", "キーワード2", "キーワード3"],
  "frontmatter": {{
    "title": "適切なタイトル",
    "tags": ["タグ1", "タグ2", "タグ3"],
    "created": "YYYY-MM-DD"
  }},
  "normalized_content": "整形済み本文"
}}
```

## 正規化ルール
- frontmatter.title: **ファイル名として使用される**ため、以下に注意:
  - ハイフン区切りではなくスペース区切りの自然な形式で記述
  - 日本語タイトルまたは自然な英語タイトルを推奨
  - ファイルシステム禁止文字（<>:"/\\|?*）を含めない
  - 200文字以内
- frontmatter.tags: 内容に基づく3-5個のタグ（日本語可）
- frontmatter.created: ファイル名から日付抽出、なければ空文字
- normalized_content:
  - 連続する空行を1行に圧縮
  - 見出しレベルを適切に調整（##から開始）
  - 箇条書きを統一（-を使用）
  - 既存のfrontmatterは削除（新規生成するため）

## 注意事項
- confidenceは判定の確信度（0.7以上で自動処理、未満は要確認）
- related_keywordsは関連ファイル検索用（3-5個）
- is_dust=trueの場合、dust_reasonに理由を記載"""


# 後方互換性のためのエイリアス（遅延評価）
# 注意: このプロンプトは動的に生成されるため、関数を直接呼び出すこと
NORMALIZER_SYSTEM_PROMPT = get_normalizer_system_prompt()
