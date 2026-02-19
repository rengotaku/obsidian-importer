# Data Model: Frontmatter ファイル振り分けスクリプト

**Date**: 2026-02-18
**Feature Branch**: `057-frontmatter-file-organizer`

## Entities

### 1. SourceFile（振り分け対象ファイル）

```
SourceFile
├── path: Path              # ファイルパス
├── filename: str           # ファイル名（拡張子含む）
├── frontmatter: dict       # パース済み frontmatter
│   ├── genre: str          # ジャンル（英語: engineer, business, economy, daily, other）
│   ├── topic: str          # トピック（任意文字列）
│   ├── title: str          # タイトル
│   ├── created: str        # 作成日
│   ├── tags: list[str]     # タグリスト
│   └── ...                 # その他のフィールド
└── content: str            # ファイル全体の内容
```

### 2. GenreMapping（ジャンルマッピング設定）

```
GenreMapping
├── mappings: dict[str, str]    # 英語 -> 日本語マッピング
│   ├── engineer: エンジニア
│   ├── business: ビジネス
│   ├── economy: 経済
│   ├── daily: 日常
│   └── other: その他
├── default_input: Path         # デフォルト入力パス
└── default_output: Path        # デフォルト出力パス
```

### 3. DistributionPlan（振り分け計画）

```
DistributionPlan
├── source_path: Path           # 元ファイルパス
├── target_dir: Path            # 振り分け先ディレクトリ
├── target_path: Path           # 振り分け先ファイルパス
├── genre_ja: str               # 日本語ジャンル名
├── topic_safe: str             # 安全化済みトピック名
└── status: DistributionStatus  # 計画ステータス
```

### 4. DistributionStatus（振り分けステータス）

```
DistributionStatus (Enum)
├── PENDING        # 処理待ち
├── SUCCESS        # 成功
├── SKIPPED        # スキップ（同名ファイル存在）
├── ERROR          # エラー（読み取り失敗等）
└── UNCLASSIFIED   # 未分類（genre/topic なし）
```

### 5. ProcessingSummary（処理サマリー）

```
ProcessingSummary
├── total: int              # 総ファイル数
├── success: int            # 成功件数
├── skipped: int            # スキップ件数
├── error: int              # エラー件数
├── unclassified: int       # 未分類件数
├── by_genre: dict[str, int]  # ジャンル別件数
└── warnings: list[str]     # 警告メッセージリスト
```

## Relationships

```
GenreMapping
    │
    └──< DistributionPlan (many) ──> SourceFile (1:1)
                │
                └──> ProcessingSummary (aggregated)
```

## State Transitions

### DistributionPlan Status Flow

```
PENDING ──┬──> SUCCESS      (移動成功)
          ├──> SKIPPED      (同名ファイル存在)
          ├──> ERROR        (読み取り/移動エラー)
          └──> UNCLASSIFIED (genre/topic なし → unclassified フォルダへ)
```

## Validation Rules

### SourceFile

1. `path` は存在する .md ファイルであること
2. `frontmatter` は YAML として有効であること
3. `genre` が存在しない場合、`unclassified` として扱う
4. `topic` が存在しない場合、空文字列として扱う

### GenreMapping

1. `mappings` は空でないこと
2. すべての値は有効なフォルダ名であること
3. `default_input` は存在するディレクトリであること
4. `default_output` は書き込み可能なパスであること

### DistributionPlan

1. `target_path` の親ディレクトリが存在するか作成可能であること
2. `topic_safe` は OS 安全な文字のみ含むこと
3. 同一 `target_path` への重複配布は禁止

## File Path Resolution

```python
# 入力
source_path = Path("data/07_model_output/organized/example.md")

# 処理
frontmatter = parse_frontmatter(source_path)
genre_en = frontmatter.get("genre", "other")        # "economy"
genre_ja = mapping.get(genre_en, "その他")          # "経済"
topic = frontmatter.get("topic", "")                # "スマートフォン"
topic_safe = sanitize_filename(topic)               # "スマートフォン"

# 出力
target_dir = output_base / genre_ja / topic_safe
# ~/Documents/Obsidian/Vaults/経済/スマートフォン/

target_path = target_dir / source_path.name
# ~/Documents/Obsidian/Vaults/経済/スマートフォン/example.md
```

## Configuration File Format

```yaml
# conf/base/genre_mapping.yml

# Genre English -> Japanese folder name mapping
genre_mapping:
  engineer: エンジニア
  business: ビジネス
  economy: 経済
  daily: 日常
  other: その他

# Default paths (overridable via CLI)
default_input: data/07_model_output/organized
default_output: ~/Documents/Obsidian/Vaults

# Fallback folder for unclassified files
unclassified_folder: unclassified
```
