# Obsidian Knowledge Base

個人ナレッジベース。Vault は `Vaults/` に集約。

## フォルダ構成

```
Obsidian/
├── Vaults/                    # コンテンツ（Vault）
│   ├── エンジニア/            # エンジニアリング・技術知識
│   ├── ビジネス/              # ビジネス関連書籍・ノート
│   ├── 経済/                  # 経済・時事ネタ
│   ├── 日常/                  # 日常生活・雑記・趣味
│   ├── その他/                # 上記に該当しないが価値のあるコンテンツ
│   └── ClaudedocKnowledges/   # プロダクト別ナレッジ（手動管理）
│
├── .staging/                  # 作業領域
│   ├── @session/              # セッション管理（ETLパイプライン）
│   │   └── YYYYMMDD_HHMMSS/   # Session（日付フォルダ）
│   │       ├── session.json   # セッションメタデータ
│   │       ├── import/        # Phase: import
│   │       │   ├── phase.json
│   │       │   ├── extract/   # Stage: Extract (input/output)
│   │       │   ├── transform/ # Stage: Transform (output)
│   │       │   └── load/      # Stage: Load (output)
│   │       └── organize/      # Phase: organize
│   │           ├── phase.json
│   │           ├── extract/
│   │           ├── transform/
│   │           └── load/
│   ├── @plan/                 # 計画・設計ドキュメント
│   ├── @test/                 # テスト用フィクスチャ
│   └── @dust/                 # ゴミ箱
│
├── src/                       # ソースコード
│   ├── etl/                   # ETL パイプライン（tenacity ベース）
│   │   ├── core/              # コア機能（Session, Phase, Stage, Step, Retry）
│   │   │   ├── status.py      # ステータス Enum（Session/Phase/Stage/Step/Item）
│   │   │   ├── types.py       # 型定義（PhaseType, StageType）
│   │   │   ├── models.py      # データモデル（ProcessingItem, StepResult, etc.）
│   │   │   ├── retry.py       # tenacity ベースのリトライ機能
│   │   │   ├── session.py     # セッション管理
│   │   │   ├── phase.py       # フェーズ管理
│   │   │   ├── stage.py       # ステージ基底クラス（JSONL ログ、DEBUG 出力、エラー詳細出力）
│   │   │   ├── step.py        # ステップトラッカー
│   │   │   └── config.py      # 設定（debug モード等）
│   │   ├── phases/            # Phase 実装（import, organize）
│   │   ├── stages/            # Stage 実装（extract, transform, load）
│   │   │   ├── extract/       # Extract Stage（ClaudeExtractor）
│   │   │   ├── transform/     # Transform Stage（KnowledgeTransformer）
│   │   │   └── load/          # Load Stage（SessionLoader）
│   │   ├── utils/             # ユーティリティモジュール（Ollama、ナレッジ抽出）
│   │   │   ├── ollama.py      # Ollama API クライアント
│   │   │   ├── knowledge_extractor.py  # 知識抽出（LLM 呼び出し）
│   │   │   ├── chunker.py     # 大規模会話チャンク分割
│   │   │   ├── file_id.py     # ファイル ID 生成（SHA256 ハッシュ）
│   │   │   └── error_writer.py # エラー詳細ファイル出力
│   │   ├── prompts/           # LLM プロンプトテンプレート
│   │   │   ├── knowledge_extraction.txt  # ナレッジ抽出プロンプト
│   │   │   └── summary_translation.txt   # 要約翻訳プロンプト
│   │   ├── tests/             # ユニットテスト
│   │   ├── cli.py             # CLI エントリポイント
│   │   └── __main__.py        # python -m src.etl 用
│   ├── converter/             # 変換スクリプト（レガシー、段階的に etl へ移行）
│   │   ├── scripts/           # Python スクリプト
│   │   │   ├── llm_import/    # LLM会話インポートパイプライン
│   │   │   ├── normalizer/    # Obsidianファイル正規化パイプライン
│   │   │   └── *.py           # 単体スクリプト
│   │   └── .venv/             # Python 仮想環境
│   └── rag/                   # RAG機能（セマンティック検索・Q&A）
│
├── .claude/                   # Claude Code 設定
├── .serena/                   # Serena MCP 設定
├── .specify/                  # Speckit 設定
├── Makefile                   # ビルド・テスト
└── CLAUDE.md                  # プロジェクト指示
```

## 主要ジャンル（自動振り分け対象）

| ジャンル | Vault | 内容 |
|---------|-------|------|
| エンジニア | `Vaults/エンジニア/` | 技術文書、プログラミング、アーキテクチャ |
| ビジネス | `Vaults/ビジネス/` | ビジネス書の要約、スキル、マネジメント |
| 経済 | `Vaults/経済/` | 経済ニュース、時事ネタ、市場分析 |
| 日常 | `Vaults/日常/` | 日常生活、雑記、趣味 |
| その他 | `Vaults/その他/` | 上記に該当しないが価値のあるコンテンツ |

---

## Kedro パイプライン用語定義

Kedro ベースのパイプライン処理で使用する用語。

| 用語 | 説明 | 例 |
|------|------|-----------|
| **Pipeline** | 処理全体を包含する DAG（有向非巡回グラフ） | `import_claude`, `import_openai`, `import_github` |
| **Node** | 単一の処理単位（純粋関数） | `parse_claude_json`, `extract_knowledge`, `classify_genre` |
| **Dataset** | ノード間で受け渡される型付きデータ | `parsed_items`, `transformed_items`, `markdown_notes` |
| **DataCatalog** | データセットの永続化先の宣言的定義 | `conf/base/catalog.yml` |

### データレイヤー構成

```
data/                                # Kedro データレイヤー
├── 01_raw/                          # 入力データ（プロバイダー固有形式）
│   ├── claude/                      # Claude エクスポート JSON
│   ├── openai/                      # ChatGPT エクスポート ZIP
│   └── github/                      # GitHub Jekyll ブログ URL
├── 02_intermediate/                 # Extract 出力（パース済みアイテム）
│   └── parsed/
├── 03_primary/                      # Transform 出力（LLM 処理済み）
│   └── transformed/
└── 07_model_output/                 # 最終 Markdown（Vault 配置前）
    ├── notes/
    └── organized/
```

### Resume（冪等再実行）

Kedro パイプラインは冪等性を持つため、同じコマンドの再実行により自動的に Resume 動作する。

- PartitionedDataset の `overwrite=false` により、出力ファイルが存在するアイテムはスキップ
- 出力ファイルが存在しないアイテムのみ再処理
- LLM 呼び出しなど高コストな処理の不要な再実行を回避

---

## 開発スクリプト構成

### `src/converter/scripts/llm_import/`

Claude会話エクスポートをObsidianノートに変換するパイプライン。

```
llm_import/
├── cli.py                 # CLIエントリポイント
├── base.py                # 基底クラス
├── providers/
│   └── claude/            # Claude固有のパーサー
│       ├── parser.py      # 会話パーサー
│       └── config.py      # 設定
├── common/
│   ├── ollama.py          # Ollama API クライアント
│   ├── chunker.py         # 大規模ファイルチャンク処理
│   ├── file_id.py         # ファイルID生成（ハッシュベース）
│   ├── retry.py           # リトライロジック
│   ├── error_writer.py    # エラーログ出力
│   ├── state.py           # 状態管理
│   ├── session_logger.py  # セッションログ
│   ├── folder_manager.py  # フォルダ管理
│   └── knowledge_extractor.py  # ナレッジ抽出
└── prompts/               # LLMプロンプトテンプレート
```

### `src/converter/scripts/normalizer/`

Obsidianファイルの正規化・整形パイプライン。

```
normalizer/
├── __main__.py            # CLIエントリポイント
├── config.py              # 設定
├── models.py              # データモデル
├── cli/                   # CLI関連
│   ├── commands.py        # コマンド実装
│   ├── parser.py          # 引数パーサー
│   ├── status.py          # ステータス表示
│   └── metrics.py         # メトリクス収集
├── pipeline/              # パイプライン処理
│   ├── runner.py          # パイプライン実行
│   ├── stages.py          # 処理ステージ定義
│   └── prompts.py         # LLMプロンプト
├── processing/            # ファイル処理
│   ├── single.py          # 単一ファイル処理
│   └── batch.py           # バッチ処理
├── validators/            # バリデーション
│   ├── title.py           # タイトル検証
│   ├── tags.py            # タグ検証
│   ├── format.py          # フォーマット検証
│   └── metadata.py        # メタデータ検証
├── detection/             # 検出ロジック
│   └── english.py         # 英語コンテンツ検出
├── io/                    # 入出力
│   ├── files.py           # ファイル操作
│   ├── session.py         # セッション管理
│   └── ollama.py          # Ollama API
├── state/                 # 状態管理
│   └── manager.py         # 状態マネージャー
└── output/                # 出力フォーマット
    ├── diff.py            # 差分表示
    └── formatters.py      # フォーマッター
```

---

## Custom Commands

### Kedro パイプライン

Kedro ベースのパイプラインは `kedro` コマンドまたは `make kedro-*` で実行。

#### Claude 会話インポート

Claude エクスポートデータから知識を抽出して Obsidian ノートに変換し、Vault に配置。

```bash
# 基本実行
kedro run --pipeline=import_claude
make kedro-run PIPELINE=import_claude

# パラメータ上書き（入力パス指定）
kedro run --pipeline=import_claude --params='{"import.input_path": "/path/to/export"}'

# 処理件数制限
kedro run --pipeline=import_claude --params='{"import.limit": 10}'

# 部分実行（特定ノードから）
kedro run --pipeline=import_claude --from-nodes=extract_knowledge

# 部分実行（特定ノードまで）
kedro run --pipeline=import_claude --to-nodes=format_markdown
```

#### ChatGPT 会話インポート

ChatGPT エクスポート ZIP から知識を抽出。

```bash
# 基本実行
kedro run --pipeline=import_openai

# ChatGPT エクスポート方法
# 1. ChatGPT 設定 → Data controls → Export data
# 2. メールで届く ZIP ファイルをダウンロード
# 3. data/01_raw/openai/ に配置
# 4. kedro run --pipeline=import_openai
```

**ChatGPT 特有の処理:**

- **ZIP 読み込み**: `conversations.json` を自動抽出
- **ツリー走査**: ChatGPT の mapping 構造を chronological order に変換
- **マルチモーダル**: 画像は `[Image: file-id]`, 音声は `[Audio: filename]` プレースホルダー
- **role 変換**: `user` → `human`, `assistant` → `assistant`, `system`/`tool` は除外

#### GitHub Jekyll ブログインポート

GitHub Jekyll ブログを git clone してインポート。

```bash
# 基本実行
kedro run --pipeline=import_github

# URL 指定
kedro run --pipeline=import_github --params='{"github.repo_url": "https://github.com/user/repo", "github.target_path": "_posts"}'
```

**GitHub Jekyll 特有の処理:**

- **git clone**: `--depth 1` + sparse-checkout で対象パスのみ高速取得
- **Jekyll frontmatter 変換**: `date` → `created`, `tags`/`categories`/`keywords` → `tags` に統合
- **日付抽出優先順位**: frontmatter.date → ファイル名（YYYY-MM-DD-*） → タイトル正規表現 → 本文正規表現 → 現在日時
- **タグ抽出**: frontmatter.tags/categories/keywords + 本文中の #hashtag を統合
- **スキップ処理**: `draft: true` または `private: true` のファイルは自動除外
- **file_id 生成**: SHA256 ハッシュで重複管理（Resume モード対応）

#### Resume（冪等再実行）

同じコマンドの再実行により、完了済みアイテムをスキップして失敗分のみ再処理。

```bash
# 前回失敗した処理の再実行（同じコマンド）
kedro run --pipeline=import_claude

# PartitionedDataset の overwrite=false により:
# - 出力ファイルが存在するアイテム → スキップ
# - 出力ファイルが存在しないアイテム → 再処理
# - LLM 呼び出しなど高コストな処理の不要な再実行を回避
```

#### DAG 可視化

パイプラインの依存関係をグラフで可視化。

```bash
# DAG 可視化サーバー起動
kedro viz
make kedro-viz

# ブラウザで http://localhost:4141 にアクセス
```

#### テスト実行

```bash
# 全テスト実行
make test
make kedro-test

# カバレッジ計測
make coverage
```

**主要機能:**

| 機能 | 説明 |
|------|------|
| Ollama 知識抽出 | LLM で会話からタイトル、要約、タグを自動抽出 |
| 冪等 Resume | 再実行で完了済みをスキップ、失敗分のみ再処理 |
| file_id 追跡 | SHA256 ハッシュで重複検出・更新管理 |
| チャンク分割 | 25000文字超の会話を複数ファイルに分割 |
| 英語 Summary 翻訳 | 英語 Summary を日本語に自動翻訳 |
| マルチモーダル対応 | ChatGPT の画像・音声をプレースホルダー処理 |
| DAG 可視化 | ノード依存関係のグラフィカル表示 |
| 部分実行 | 特定ノード範囲のみ実行可能 |

**スキップ条件:**

- メッセージ数 < 3（MIN_MESSAGES）: 短すぎる会話をスキップ

**エッジケース対応:**

- 空の conversations.json: 警告ログを出力して正常終了
- 破損した ZIP ファイル: エラーメッセージを出力して終了
- タイトル欠損: 最初のユーザーメッセージから生成
- タイムスタンプ欠損: 現在日時にフォールバック

**データフロー:**

```
data/01_raw/claude/*.json          ← 入力（Claude エクスポート）
    ↓ [extract_claude pipeline]
data/02_intermediate/parsed/*.json ← パース済みアイテム
    ↓ [transform pipeline]
data/03_primary/transformed/*.json ← LLM 処理済みアイテム
    ↓ [transform pipeline - format_markdown]
data/07_model_output/notes/*.md    ← 最終 Markdown
    ↓ [organize pipeline]
Vaults/エンジニア/*.md             ← Vault 配置
```
Total Processing Time: 53761ms
Overall Change: 1964 → 1219 chars (ratio: 0.621)
```

**使用例:**

- 処理時間のボトルネック特定
- 各ステップでの content 変化量の確認
- チャンク分割されたアイテムの追跡
- LLM 処理の効果測定

**エラー詳細表示（`SHOW_ERROR_DETAILS=1`）:**

`--show-error-details` フラグを使用すると、`error_details.jsonl` からエラー詳細を表示します。

| 項目 | 説明 |
|------|------|
| Timestamp | エラー発生時刻 |
| Stage | ステージ名（transform, load など） |
| Step | ステップ名（extract_knowledge など） |
| Error Type | 例外クラス名 |
| Error Message | エラーメッセージ |
| Backtrace | フルスタックトレース（20行まで表示） |
| Metadata | LLM プロンプト/出力などの追加情報（500文字まで表示） |

```bash
# エラー詳細を表示
make item-trace SESSION=20260126_144122 TARGET=ERROR SHOW_ERROR_DETAILS=1
```

**注意:**

- `debug/steps.jsonl` が存在するセッションのみ対応
- セッション実行時に `--debug` または `DEBUG=1` が必須

#### 終了コード

| Code | 意味 |
|------|------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 入力ファイル/セッションが見つからない |
| 3 | Ollama 接続エラー |
| 4 | 部分成功（一部失敗） |
| 5 | 全件失敗 |

---

## ファイル正規化ルール

### 正規化ステータス

frontmatter の `normalized` プロパティで判別:

```yaml
---
title: ファイルのタイトル
normalized: true    # 正規化済み
created: 2022-10-17
file_id: abc123     # ファイル追跡用ID（ハッシュ）
---
```

| 状態 | `normalized` |
|------|--------------|
| **正規化済み** | `true` |
| **未正規化** | `false` または未設定 |

### 正規化時の処理

1. **frontmatter 追加/更新**:
   - `title`: ファイルのタイトル
   - `created`: 作成日（Jekyll形式から抽出 or 現在日）
   - `tags`: 適切なタグ
   - `normalized: true`
   - `file_id`: ファイル追跡用ハッシュ（自動生成）

2. **不要フィールド削除**:
   - `draft`, `private`, `slug`, `lastmod`, `keywords` (Jekyll特有)

3. **ファイル名**: タイトルのみに変更
   - Before: `2022-10-17-Online-DDL-of-mysql.md`
   - After: `Online DDL of mysql.md`

### 未正規化ファイルの検出

```bash
# normalizedプロパティがないファイルを検出
grep -rL "normalized: true" --include="*.md" .
```

---

## Obsidian Markdown Conventions

### 1. YAML Frontmatter (Required)

```yaml
---
title: ファイルのタイトル
tags:
  - タグ1
  - タグ2
created: YYYY-MM-DD
related:
  - "[[関連ファイル1]]"
  - "[[関連ファイル2]]"
---
```

### 2. Internal Links

- Wiki-style: `[[ファイル名]]`
- Display text: `[[ファイル名|表示テキスト]]`
- Heading link: `[[ファイル名#見出し]]`

### 3. Callouts

```markdown
> [!quote] 引用
> メッセージ

> [!note] メモ
> 補足情報

> [!warning] 警告
> 注意事項

> [!tip] ヒント
> 役立つ情報

> [!example] 例
> 具体例
```

### 4. Structure

- `##` メインセクション
- `###` サブセクション
- `####` 詳細トピック
- 末尾に「関連」セクションで内部リンク

### 5. Formatting

- 空行は最大1行
- ネストはタブでインデント
- 強調は `**太字**`
- リストは `-` を使用

### 6. Tags

- frontmatter 内に記載（インライン `#tag` は避ける）
- Vault 共通タグ例:
  - `#status/draft`, `#status/done`
  - `#type/note`, `#type/summary`, `#type/reference`

---

## ジャンル別振り分け基準

### エンジニア へ振り分け

- プログラミング言語、フレームワーク
- システム設計、アーキテクチャ
- DevOps、インフラ
- 技術的なベストプラクティス

### ビジネス へ振り分け

- ビジネス書の要約・メモ
- コミュニケーション、話し方
- マネジメント、リーダーシップ
- キャリア、自己啓発

### 経済 へ振り分け

- 経済ニュース、市場動向
- 企業分析、業界動向
- 投資、金融
- 政策、規制

### 日常 へ振り分け

- 日常生活のメモ
- 趣味、娯楽
- 雑記、アイデア

### その他 へ振り分け

- 上記カテゴリに明確に該当しないもの
- 複数カテゴリにまたがるもの
- 分類が困難だが価値のあるコンテンツ

### ClaudedocKnowledges（自動振り分け対象外）

手動管理のみ。プロダクト固有のナレッジベース。

---

## Claude 作業時のルール

- 各 Vault の CLAUDE.md があればそちらを優先
- ファイル移動前に既存構造を確認
- 日本語ファイル名可
- 大量ファイル処理時は確認を求める
- **Python スクリプト実行時は必ず venv を使用**: `.venv/bin/python` または `make` コマンド
- **レガシーコード (`src/converter/`) は一切修正しない**: Kedro パイプライン (`src/obsidian_etl/`) のみを修正対象とする

---

## エラー記録機能

ETL パイプライン実行時、エラーが発生すると以下の2箇所に記録されます：

### 1. `pipeline_stages.jsonl` - 基本情報

各アイテムの処理結果を記録。エラー時は `status: "failed"` と `error_message` が記録されます。

```jsonl
{
  "timestamp": "2026-01-26T08:00:00.000000+00:00",
  "session_id": "20260126_080000",
  "filename": "conversation.json",
  "stage": "transform",
  "step": "extract_knowledge",
  "timing_ms": 5000,
  "status": "failed",
  "error_message": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)"
}
```

**記録内容:**
- エラーステータス (`status: "failed"`)
- エラーメッセージ (`error_message`)
- 処理時間、文字数変化などの基本メトリクス

### 2. `error_details.jsonl` - 詳細情報

エラーの詳細情報をデバッグ用に記録。`item_id` で引き当て可能。

```jsonl
{
  "timestamp": "2026-01-26T08:00:00.000000",
  "session_id": "20260126_080000",
  "item_id": "conversation_12345",
  "stage": "transform",
  "step": "extract_knowledge",
  "error_type": "JSONDecodeError",
  "error_message": "Expecting value: line 1 column 1 (char 0)",
  "backtrace": "Traceback (most recent call last):\n  File ...",
  "metadata": {
    "conversation_title": "...",
    "llm_prompt": "...",
    "llm_output": "..."
  }
}
```

**記録内容:**
- 例外タイプ (`error_type`)
- エラーメッセージ (`error_message`)
- フルバックトレース (`backtrace`)
- LLM プロンプト・出力などのメタデータ

### エラートレース

`make item-trace` コマンドで、エラーが発生したアイテムの処理履歴を確認できます：

```bash
# エラーアイテムすべてをトレース
make item-trace SESSION=20260126_080000 TARGET=ERROR

# 特定アイテムをトレース
make item-trace SESSION=20260126_080000 ITEM=conversation_12345
```

---

## 開発・テスト

**テストフレームワーク**: Python 標準ライブラリの `unittest` を使用（pytest 不使用）

**テスト実行は Makefile を使用する**:

```bash
make test      # 全テスト実行（ユニット + 統合）
make check     # Python 構文チェック
make lint      # コード品質チェック (ruff)
```

| ターゲット | 説明 |
|-----------|------|
| `make test` | ユニットテスト（Kedro パイプライン） |
| `make coverage` | テストカバレッジ計測（≥80%） |
| `make kedro-run` | Kedro パイプライン実行 |
| `make kedro-test` | Kedro テスト実行 |
| `make kedro-viz` | DAG 可視化 |

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+（標準ライブラリ中心） |
| パイプライン | Kedro 1.1.1 + kedro-datasets |
| LLM | Ollama API（ローカル） |
| データ形式 | Markdown, JSON, JSONL |
| テスト | unittest（標準ライブラリ） |
| Lint | ruff（オプション） |
| ファイル追跡 | file_id（SHA256ハッシュベース） |

## Active Technologies
- Python 3.11+ + haystack-ai, ollama-haystack, qdrant-haystack (001-rag-migration-plan)
- Qdrant (ローカルファイル永続化 @ `data/qdrant/`) (001-rag-migration-plan)
- Python 3.11+ + Kedro 1.1.1, kedro-datasets, tenacity 8.x, PyYAML 6.0+, requests 2.28+ (044-kedro-migration)
- ファイルシステム（JSON, JSONL, Markdown）、Kedro DataCatalog（PartitionedDataset） (044-kedro-migration)

## Recent Changes
- 044-kedro-migration: Migrated from custom ETL pipeline (`src/etl/`) to Kedro 1.1.1. Removed session management, introduced DAG-based pipelines (import_claude, import_openai, import_github), idempotent resume via PartitionedDataset
