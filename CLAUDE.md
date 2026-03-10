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
│   ├── 05_model_input/        # モデル入力（JSON）
│   │   ├── classified/        # ジャンル分類済みデータ
│   │   ├── cleaned/           # クリーンアップ済みデータ
│   │   ├── normalized/        # 正規化済みデータ
│   │   ├── topic_extracted/   # トピック抽出済みデータ
│   │   ├── vault_determined/  # Vault 振り分け済みデータ
│   │   └── organized/         # 整理済みデータ（JSON）
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
├── specs/                     # 設計・仕様ドキュメント
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
                  → data/05_model_input/classified/*.json
                  → data/05_model_input/normalized/*.json
                  → data/07_model_output/notes/*.md
                  → data/07_model_output/organized/*.md
```

### プロバイダー別処理

**Claude**: ZIP → `conversations.json` 抽出 → UUID で会話識別

**ChatGPT**: ZIP → mapping 構造を chronological order に変換 → 画像/音声はプレースホルダー

**GitHub Jekyll**: git clone → frontmatter 変換（`date` → `created`）

---

## 開発・テスト

```bash
make test            # 全テスト実行（unit test）
make coverage        # カバレッジ計測（≥80%）
make lint            # コード品質チェック (ruff + pylint)
make ruff            # ruff のみ実行
make pylint          # pylint のみ実行
make kedro-viz       # DAG 可視化
make test-e2e        # E2E テスト（ゴールデンファイル比較）
make test-e2e-golden # ゴールデンファイル品質テスト
make test-integration       # 統合テスト（モックモード、Ollama 不要）
make test-golden-responses  # ゴールデンレスポンス再生成（要 Ollama）[MODEL=gemma3:12b]
```

**CI**: GitHub Actions で PR 作成時および main push 時に `make test` + `make test-integration` + `make lint` を自動実行

### テスト方針

| テスト種別 | コマンド | 検証内容 | Ollama |
|-----------|---------|---------|:------:|
| Unit test | `make test` | 異常系（LLM失敗、圧縮率不足、空レスポンス、review振り分け等）| 不要 |
| 統合テスト | `make test-integration` | 正常系 E2E（パイプライン全体がゴールデンレスポンスで動作）| 不要 |
| E2E テスト | `make test-e2e` | 実LLMでの品質検証（ゴールデンファイル比較）| **必要** |

- **正常系**: `test-integration` でゴールデンレスポンス（実LLM出力）を使い、パイプライン全体の結合を検証
- **異常系**: `make test` の unit test で mock/patch ベースで網羅（圧縮率、LLMエラー、review振り分け等）
- 統合テストは正常系のみ。異常系を統合テストに含める必要はない

### テストフィクスチャ

- **ゴールデンファイル**（E2E用）: `tests/fixtures/golden/` — LLM まとめ品質の検証
- **ゴールデンレスポンス**（統合テスト用）: `tests/fixtures/golden_responses/` — 実 LLM 出力のモックレスポンス

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
| LLM | Ollama API（ローカル）、デフォルトモデル: `gpt-oss-swallow:20b` |
| データ形式 | Markdown, JSON, JSONL |
| テスト | unittest（標準ライブラリ） |
| Lint | ruff + pylint |

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

ジャンル定義は `conf/base/genre_mapping.yml` を参照。

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

### コマンド実行

- **`make` ターゲットを使う**: テスト・lint・パイプライン実行は直接コマンド（`pytest`, `ruff`, `kedro run`）ではなく `make` 経由で実行する（環境変数・venv が自動設定される）
- Python を直接実行する場合は `.venv/bin/python` を使用

### LLM モデル・設定

- **モデル名の正**: `conf/base/parameters.yml` の `ollama.defaults.model` が唯一の正。コード内やドキュメントからモデル名を推測しない
- **LLM 設定は用途別に分離**: 新しい `call_ollama` 呼び出しを追加する場合、`parameters.yml` に専用の設定キーを追加する。既存キーを別用途で流用しない（`num_predict` 不足による出力切断の原因になる）

### 変更時の影響範囲

- **パイプライン横断チェック**: パイプラインや設定を変更したら、同じパターンが他パイプライン（`src/**/pipeline.py`）にないか検索する
- **ゴールデンレスポンス再生成**: プロンプト変更・テストフィクスチャ変更・モデル変更時は `make test-golden-responses` で再生成が必要
