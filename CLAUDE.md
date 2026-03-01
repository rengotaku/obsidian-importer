# Obsidian Knowledge Base

LLM 会話履歴を Obsidian ナレッジベースに変換するパイプライン。

## プロジェクト方針

| 方針 | 説明 |
|------|------|
| **後方互換性は考慮しない** | 破壊的変更を躊躇なく行う |
| **シンプルさ優先** | 冗長な構造より、明確で簡潔な設計を選択 |

## フォルダ構成

```
obsidian-importer/
├── data/                      # Kedro データレイヤー
│   ├── 01_raw/                # 入力（ZIP）
│   ├── 02_intermediate/       # パース済み
│   ├── 03_primary/            # LLM 処理済み
│   └── 07_model_output/       # 最終 Markdown
│       ├── notes/             # 通常出力
│       ├── review/            # レビュー対象（圧縮率低）
│       ├── organized/         # ジャンル分類済み
│       └── organized_review/  # 分類済みレビュー対象
│
├── src/obsidian_etl/          # Kedro パイプライン（現行）
├── src/rag/                   # RAG 機能
├── conf/                      # Kedro 設定
├── tests/                     # テスト
└── Makefile                   # ビルド・テスト
```

---

## Kedro パイプライン

### 基本コマンド

```bash
# 初回セットアップ
make setup

# Vault Output 設定（初回のみ）
cp conf/base/parameters_organize.local.yml.example conf/local/parameters_organize.yml
# vault_base_path を自分の環境に合わせて編集

# パイプライン実行（デフォルト: Claude）
kedro run

# プロバイダー指定
kedro run --pipeline=import_claude
kedro run --pipeline=import_openai
kedro run --pipeline=import_github

# 処理件数制限
kedro run --params='{"import.limit": 10}'

# 部分実行
kedro run --from-nodes=extract_knowledge
kedro run --to-nodes=format_markdown
```

### データフロー

```
data/01_raw/*.zip → data/02_intermediate/parsed/*.json
                  → data/03_primary/transformed/*.json
                  → data/07_model_output/notes/*.md
                  → data/07_model_output/organized/*.md
```

### 主要機能

| 機能 | 説明 |
|------|------|
| Ollama 知識抽出 | LLM でタイトル、要約、タグを自動抽出 |
| 冪等 Resume | 再実行で完了済みスキップ（PartitionedDataset） |
| file_id 追跡 | SHA256 ハッシュで重複検出 |
| チャンク分割 | 25000文字超を複数ファイルに分割 |
| 圧縮率検証 | 過度な圧縮を検出し `review/` に出力 |

### プロバイダー別処理

**Claude**: ZIP → `conversations.json` 抽出 → UUID で会話識別

**ChatGPT**: ZIP → mapping 構造を chronological order に変換 → 画像/音声はプレースホルダー

**GitHub Jekyll**: git clone → frontmatter 変換（`date` → `created`）

---

## 開発・テスト

```bash
make test            # 全テスト実行
make coverage        # カバレッジ計測（≥80%）
make lint            # コード品質チェック (ruff + pylint)
make ruff            # ruff のみ実行
make pylint          # pylint のみ実行
make kedro-viz       # DAG 可視化
make test-e2e        # E2E テスト（ゴールデンファイル比較）
make test-e2e-golden # ゴールデンファイル品質テスト
```

**CI**: GitHub Actions で PR 作成時および main push 時に `make ruff` と `make pylint` を自動実行

### ゴールデンファイル

**場所**: `tests/fixtures/golden/`

**目的**: LLM まとめ品質の継続的検証

**ファイル数**: 10 件（カテゴリ別選定）

**カテゴリ**:
- 技術系（小・中・大）
- ビジネス系（小・中）
- 日常系（小）
- 表形式データ（中・大）
- コード含む（小・中）

**品質基準**:
- 圧縮率しきい値を満たす（10-20%、サイズ依存）
- 表形式データが Markdown テーブルで保持
- コードブロックが保持
- review フォルダに振り分けられない品質

### 終了コード

| Code | 意味 |
|------|------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 入力ファイル未発見 |
| 3 | Ollama 接続エラー |
| 4 | 部分成功 |
| 5 | 全件失敗 |

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+（標準ライブラリ中心） |
| パイプライン | Kedro 1.1.1 + kedro-datasets |
| LLM | Ollama API（ローカル） |
| データ形式 | Markdown, JSON, JSONL |
| テスト | unittest（標準ライブラリ） |
| Lint | ruff |

---

## Obsidian Markdown Conventions

### YAML Frontmatter (必須)

```yaml
---
title: タイトル
tags:
  - タグ1
created: YYYY-MM-DD
normalized: true
file_id: abc123
---
```

### 記法

- 内部リンク: `[[ファイル名]]`, `[[ファイル名|表示]]`, `[[ファイル名#見出し]]`
- Callouts: `> [!note]`, `> [!warning]`, `> [!tip]`, `> [!example]`
- 見出し: `##` メイン, `###` サブ, `####` 詳細
- リスト: `-` を使用、ネストはタブ

### 正規化ルール

1. **frontmatter**: `title`, `created`, `tags`, `normalized: true`, `file_id` を追加
2. **不要フィールド削除**: `draft`, `private`, `slug`, `lastmod`, `keywords`
3. **ファイル名**: タイトルのみ（日付プレフィックス削除）

---

## ジャンル別振り分け

| ジャンル | 内容 |
|---------|------|
| AI | AI/ML、生成AI、機械学習、Claude、ChatGPT |
| DevOps | インフラ、クラウド、CI/CD、Docker、Kubernetes |
| エンジニア | プログラミング、アーキテクチャ、API、データベース |
| 経済 | 経済ニュース、投資、金融、市場 |
| ビジネス | ビジネス、マネジメント、リーダーシップ、マーケティング |
| 健康 | 健康、医療、フィットネス、運動 |
| 子育て | 子育て、育児、教育、キッザニア |
| 旅行 | 旅行、観光、ホテル |
| ライフスタイル | 家電、DIY、住居、生活用品 |
| 日常 | 日記、趣味、雑記 |
| その他 | 上記に該当しないコンテンツ |

---

## 圧縮率検証

| 元サイズ | しきい値 |
|---------|---------|
| 10,000文字以上 | 10% |
| 5,000-9,999文字 | 15% |
| 5,000文字未満 | 20% |

しきい値未達のファイルは `review/` に出力され、`review_reason` フィールドが追加される。

---

## Claude 作業時のルール

- 各 Vault の CLAUDE.md があればそちらを優先
- ファイル移動前に既存構造を確認
- 日本語ファイル名可
- 大量ファイル処理時は確認を求める
- **Python 実行は venv 使用**: `.venv/bin/python` または `make`

## Active Technologies
- Python 3.11+ (Python 3.13 compatible) + Kedro 1.1.1, kedro-datasets, requests (Ollama API), PyYAML 6.0+ (052-improve-summary-quality)
- ファイルシステム (Markdown, JSON, JSONL)、Kedro PartitionedDataset (052-improve-summary-quality)
- Python 3.11+ (既存プロジェクト準拠) + PyYAML (既存依存関係) (057-frontmatter-file-organizer)
- ファイルシステム（Markdown ファイル） (057-frontmatter-file-organizer)
- Python 3.11+ (Python 3.13 compatible) + Kedro 1.1.1, kedro-datasets, PyYAML 6.0+ (058-refine-genre-classification)
- ファイルシステム (PartitionedDataset) (058-refine-genre-classification)
- ファイルシステム (PartitionedDataset for input, 直接ファイルコピー for output) (059-organize-vault-output)
- Python 3.11+ (Python 3.13 compatible) + Kedro 1.1.1, kedro-datasets, PyYAML 6.0+, requests (Ollama API) (060-dynamic-genre-config)
- ファイルシステム (YAML, Markdown, JSON) (060-dynamic-genre-config)
- Python 3.11+ + ruff (既存), pylint (新規追加) (061-github-actions-lint)
- Python 3.11+（Python 3.13 compatible） + Kedro 1.1.1, kedro-datasets, requests (urllib) (062-warmup-fail-stop)

## Recent Changes
- 052-improve-summary-quality: Added Python 3.11+ (Python 3.13 compatible) + Kedro 1.1.1, kedro-datasets, requests (Ollama API), PyYAML 6.0+
