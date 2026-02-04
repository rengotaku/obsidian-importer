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

## パイプライン用語定義

ETL パイプライン処理で使用する階層構造の用語。フォルダ名として使用される。

| 用語 | 説明 | フォルダ例 |
|------|------|-----------|
| **Session** | 処理全体を包含する単位。日付時刻で識別 | `20260119_143052/` |
| **Phase** | Session 内の処理種別 | `import/`, `organize/` |
| **Stage** | Phase を ETL パターンで分割 | `extract/`, `transform/`, `load/` |
| **Step** | Stage 内の具体的な処理単位 | `parse_json`, `validate`, `generate_metadata` |

### セッションフォルダ構成

```
.staging/@session/
└── 20260119_143052/                    # Session
    ├── session.json                    # セッションメタデータ
    ├── import/                         # Phase
    │   ├── phase.json                  # Phase ステータス（Step 単位で更新）
    │   ├── extract/                    # Stage: Extract
    │   │   ├── input/                  # 入力データ（Claude エクスポート等）
    │   │   └── output/                 # 抽出結果
    │   ├── transform/                  # Stage: Transform
    │   │   └── output/                 # 変換結果
    │   └── load/                       # Stage: Load
    │       └── output/                 # 最終出力
    └── organize/                       # Phase
        ├── phase.json
        ├── extract/
        │   ├── input/
        │   └── output/
        ├── transform/
        │   └── output/
        └── load/
            └── output/                 # Vaults への移動候補
```

### debug モード

| モード | ステータス JSON | 詳細ログ |
|--------|----------------|---------|
| 通常 | ✅ 出力（常時） | ❌ なし |
| debug | ✅ 出力（常時） | ✅ 各 Stage に出力 |

### session.json 形式

セッションのメタデータと各フェーズの処理結果を記録する JSON ファイル。

```json
{
  "session_id": "20260124_164549",
  "created_at": "2026-01-24T16:45:49.417261",
  "status": "completed",
  "phases": {
    "import": {
      "status": "completed",
      "success_count": 5,
      "error_count": 1,
      "skipped_count": 0,
      "completed_at": "2026-01-24T16:45:49.417945"
    },
    "organize": {
      "status": "crashed",
      "success_count": 0,
      "error_count": 0,
      "skipped_count": 0,
      "completed_at": "2026-01-24T16:50:12.123456",
      "error": "ValueError: Invalid vault path"
    }
  },
  "debug_mode": false
}
```

**フィールド定義**:

| フィールド | 型 | 説明 |
|----------|-----|------|
| `session_id` | string | セッション識別子（YYYYMMDD_HHMMSS 形式） |
| `created_at` | string | セッション作成日時（ISO 8601 形式） |
| `status` | string | セッション全体のステータス（`in_progress`, `completed`, `failed`） |
| `phases` | dict | 各フェーズの処理結果（キーはフェーズ名） |
| `debug_mode` | boolean | debug モードで実行されたかどうか |

**PhaseStats フィールド**（`phases` の各値）:

| フィールド | 型 | 説明 |
|----------|-----|------|
| `status` | string | フェーズのステータス（`completed`, `partial`, `failed`, `crashed`） |
| `success_count` | int | 成功したアイテム数 |
| `error_count` | int | 失敗したアイテム数 |
| `skipped_count` | int | スキップされたアイテム数（Resume モード時）。デフォルト: 0 |
| `completed_at` | string | フェーズ完了日時（ISO 8601 形式） |
| `error` | string (optional) | クラッシュ時のエラーメッセージ（status="crashed" の場合のみ） |

**ステータスの意味**:

| Status | 説明 |
|--------|------|
| `completed` | すべてのアイテムが正常に処理された |
| `partial` | 一部のアイテムが失敗したが、一部は成功した |
| `failed` | すべてのアイテムが失敗した |
| `crashed` | 予期しない例外でフェーズが中断された |

**後方互換性**: 旧形式の `phases: ["import"]` も読み込み可能（`Session.from_dict()` で自動変換）

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

### ETL パイプライン（新）

新しい ETL パイプラインは `python -m src.etl` または `make` コマンドで実行。

#### `import` / LLM会話インポート

Claude または ChatGPT エクスポートデータから知識を抽出して Obsidian ノートに変換。

```bash
# Claude インポート
make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude  # 全件処理
make import INPUT=... PROVIDER=claude DRY_RUN=1                    # プレビュー
make import INPUT=... PROVIDER=claude DEBUG=1                      # debug モード
make import INPUT=... PROVIDER=claude LIMIT=5                      # 件数制限

# ChatGPT インポート
make import INPUT=chatgpt_export.zip PROVIDER=openai  # ZIP ファイル指定
make import INPUT=... PROVIDER=openai DEBUG=1         # debug モード

# 複数 INPUT 指定（カンマ区切り）
make import INPUT=export1.zip,export2.zip PROVIDER=openai  # 複数 ZIP を 1 セッションで処理

# GitHub Jekyll ブログインポート（URL 入力）
make import INPUT=https://github.com/user/repo/tree/master/_posts INPUT_TYPE=url PROVIDER=github
make import INPUT=... INPUT_TYPE=url PROVIDER=github LIMIT=10  # 件数制限
make import INPUT=... INPUT_TYPE=url PROVIDER=github DEBUG=1   # debug モード

# 既存セッション再利用（Resume モード）- PROVIDER 不要
make import SESSION=20260119_143052     # 指定セッションで続行

# 直接実行
python -m src.etl import --input PATH [--input PATH ...] --provider claude|openai|github [--input-type path|url] [--session ID] [--debug] [--dry-run] [--limit N]
```

**INPUT_TYPE パラメータ:**

| 値 | デフォルト | 説明 |
|----|-----------|------|
| `path` | ✅ | ローカルファイル/ディレクトリ。`Path.exists()` チェック後コピー |
| `url` | | リモート URL（GitHub 等）。URL フォーマットチェック後 `url.txt` に保存 |

**複数 INPUT 指定:**

- Makefile: カンマ区切り `INPUT=a.zip,b.zip`
- CLI: 複数回指定 `--input a.zip --input b.zip`
- `INPUT_TYPE` は全 INPUT に適用される（混在不可）

**サポートプロバイダー:**

| プロバイダー | 入力形式 | 指定方法 |
|------------|---------|---------|
| Claude (デフォルト) | JSON ファイル | `--provider claude` または省略 |
| ChatGPT | ZIP ファイル | `--provider openai` |
| GitHub | GitHub URL | `--provider github` |

**主要機能:**

| 機能 | 説明 |
|------|------|
| Ollama 知識抽出 | LLM で会話からタイトル、要約、タグを自動抽出 |
| Resume モード | `--session` で中断されたインポートを再開。Extract output（data-dump-*.jsonl）を再利用し、処理済みアイテムをスキップして LLM 呼び出しを回避 |
| file_id 追跡 | SHA256 ハッシュで重複検出・更新管理 |
| チャンク分割 | 25000文字超の会話を複数ファイルに分割 |
| 英語 Summary 翻訳 | 英語 Summary を日本語に自動翻訳 |
| エラー詳細出力 | errors/ フォルダに LLM プロンプト・出力を保存 |
| マルチモーダル対応 | ChatGPT の画像・音声をプレースホルダー処理 |

**スキップ条件:**

- メッセージ数 < 3（MIN_MESSAGES）: 短すぎる会話をスキップ

**エッジケース対応:**

- 空の conversations.json: 警告ログを出力して正常終了
- 破損した ZIP ファイル: エラーメッセージを出力して終了コード 2
- タイトル欠損: 最初のユーザーメッセージから生成
- タイムスタンプ欠損: 現在日時にフォールバック

**出力フォルダ構成:**

```
.staging/@session/YYYYMMDD_HHMMSS/import/
├── phase.json                   # Phase ステータス
├── errors/                      # エラー詳細（conversation_id.md）
├── extract/
│   ├── input/                   # Claude: JSON, ChatGPT: ZIP
│   └── output/                  # パース済み会話データ（data-dump-{番号4桁}.jsonl、1000レコード/ファイル）
├── transform/
│   └── output/                  # 知識抽出結果
└── load/
    └── output/
        └── conversations/       # 最終 Markdown ファイル
```

**ChatGPT エクスポート方法:**

1. ChatGPT 設定 → Data controls → Export data
2. メールで届く ZIP ファイルをダウンロード
3. `make import INPUT=chatgpt_export.zip PROVIDER=openai` でインポート

**ChatGPT 特有の処理:**

- **ZIP 読み込み**: `conversations.json` を自動抽出
- **ツリー走査**: ChatGPT の mapping 構造を chronological order に変換
- **マルチモーダル**: 画像は `[Image: file-id]`, 音声は `[Audio: filename]` プレースホルダー
- **role 変換**: `user` → `human`, `assistant` → `assistant`, `system`/`tool` は除外

**GitHub Jekyll ブログ特有の処理:**

- **git clone**: `--depth 1` + sparse-checkout で対象パスのみ高速取得
- **Jekyll frontmatter 変換**: `date` → `created`, `tags`/`categories`/`keywords` → `tags` に統合
- **日付抽出優先順位**: frontmatter.date → ファイル名（YYYY-MM-DD-*） → タイトル正規表現 → 本文正規表現 → 現在日時
- **タグ抽出**: frontmatter.tags/categories/keywords + 本文中の #hashtag を統合
- **スキップ処理**: `draft: true` または `private: true` のファイルは自動除外
- **file_id 生成**: SHA256 ハッシュで重複管理（Resume モード対応）

**GitHub 入力例:**

```bash
# 基本形式
make import INPUT=https://github.com/user/repo/tree/master/_posts PROVIDER=github

# 実際の例
make import INPUT=https://github.com/example-user/example-user.github.io/tree/master/_posts PROVIDER=github LIMIT=5
```

#### `organize` / ファイル整理

```bash
make organize INPUT=.staging/@session/YYYYMMDD_HHMMSS/import/load/output/conversations/  # 全件処理
make organize INPUT=... DRY_RUN=1       # プレビュー

# 直接実行
python -m src.etl organize --input PATH [--debug] [--dry-run] [--limit N]
```

#### `status` / セッション状態確認

```bash
make status ALL=1                       # 全セッション表示
make status SESSION=20260119_143052     # 特定セッション
make status SESSION=... JSON=1          # JSON 出力

# 直接実行
python -m src.etl status [--session ID] [--all] [--json]
```

#### `retry` / 失敗アイテムのリトライ

```bash
make retry SESSION=20260119_143052       # 全 Phase リトライ
make retry SESSION=... PHASE=import      # 特定 Phase のみ

# 直接実行
python -m src.etl retry --session ID [--phase TYPE] [--debug]
```

#### `session-clean` / 古いセッション削除

```bash
make session-clean DAYS=7 DRY_RUN=1   # プレビュー
make session-clean DAYS=7 FORCE=1     # 確認なしで削除

# 直接実行
python -m src.etl clean [--days N] [--dry-run] [--force]
```

#### `item-trace` / アイテム処理の詳細トレース

指定したアイテムの全処理ステップを時系列で表示。debug モード（`--debug`）で実行されたセッションのみ対応。

```bash
# 特定アイテムのトレース（TARGET=ALL がデフォルト）
make item-trace SESSION=20260119_143052 ITEM=conversation_uuid  # 基本トレース
make item-trace SESSION=... ITEM=... SHOW_CONTENT=1            # content 差分も表示

# エラーアイテムすべてをトレース
make item-trace SESSION=20260119_143052 TARGET=ERROR            # エラーアイテムを自動抽出
make item-trace SESSION=... TARGET=ERROR SHOW_ERROR_DETAILS=1  # エラー詳細も表示

# 直接実行
python -m src.etl trace --session ID --target ALL --item ITEM_ID [--show-content] [--show-error-details]
python -m src.etl trace --session ID --target ERROR [--show-content] [--show-error-details]
```

**TARGET パラメータ:**

| 値 | 説明 | ITEM パラメータ |
|----|------|----------------|
| `ALL` (デフォルト) | 特定アイテムをトレース | 必須 |
| `ERROR` | エラーになったアイテムすべてをトレース | 不要（自動抽出） |

**表示内容:**

| 項目 | 説明 |
|------|------|
| Step | ステップ番号（各 stage ごと） |
| Phase | 処理フェーズ（import, organize） |
| Stage | ETL ステージ（extract, transform, load） |
| Current Step | ステップ名（extract_knowledge, format_markdown など） |
| Before | 処理前の文字数 |
| After | 処理後の文字数 |
| Ratio | 変化率（after / before） |
| Time(ms) | 処理時間（ミリ秒） |

**出力例:**

```
Step   Phase      Stage      Current Step              Before     After      Ratio    Time(ms)
================================================================================================
1      import     transform  extract_knowledge         1964       1964       1.000    53761
2      import     transform  generate_metadata         1964       1964       1.000    0
3      import     transform  format_markdown           1964       1219       0.621    0
1      import     load       write_to_session          1964       1219       0.621    0
2      import     load       update_index              1964       1219       0.621    0
================================================================================================
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

### レガシーコマンド

以下は旧実装。新 ETL パイプラインへの移行中は両方利用可能。

### `Claude解析` / `claudeデータ解析`

`.staging/@index/claude/` 内の Claude エクスポートデータを解析して Obsidian ノートに変換:

```bash
python3 scripts/parse_claude_export.py <export_dir> --output <output_dir>
```

**解析対象:**
- `conversations.json` → 会話ごとの Markdown ファイル
- `memories.json` → Claude が記憶しているコンテキスト
- `projects.json` → プロジェクト一覧

**出力:**
- `Claude_Export_Index.md` - 統計とインデックス
- `Claude_Memories.md` - メモリーデータ
- `Claude_Projects.md` - プロジェクト一覧
- `conversations/` - 個別会話ファイル

---

### `整理して` / `organize`

セッション内のファイルを適切な Vault へ振り分ける（セッションベース処理）:

```bash
make organize                    # 全件処理
make organize ACTION=preview     # プレビュー（処理なし）
make organize DEBUG=1            # debug モード
```

**処理フロー（ETL パターン）:**

| Stage | 処理内容 | 入力 | 出力 |
|-------|---------|------|------|
| Extract | ファイル読み込み・メタデータ抽出 | `extract/input/` | `extract/output/` |
| Transform | ジャンル判定・フォーマット正規化 | Extract 出力 | `transform/output/` |
| Load | Vault への配置 | Transform 出力 | `load/output/` → Vaults |

**ジャンル判定:**
- 技術・エンジニアリング → `Vaults/エンジニア/`
- ビジネス・マネジメント → `Vaults/ビジネス/`
- 経済・時事ネタ → `Vaults/経済/`
- 日常・雑記・趣味 → `Vaults/日常/`
- 上記に該当しない → `Vaults/その他/`
- **※ `Vaults/ClaudedocKnowledges/` には自動振り分けしない（手動管理）**

**フォーマット正規化:**
- YAML frontmatter 追加
- 内部リンク `[[]]` 形式に変換
- 適切な callout 使用
- 余分な空行削除

**セッション出力先:** `.staging/@session/YYYYMMDD_HHMMSS/organize/`

---

### `llm-import` / `Claude会話インポート`

Claude 会話データをナレッジとして抽出（セッションベース処理）:

```bash
make llm-import                  # 全件処理
make llm-import ACTION=preview   # プレビュー（処理なし）
make llm-import ACTION=status    # 処理状態確認
make llm-import DEBUG=1          # debug モード（詳細ログ出力）
```

**処理フロー（ETL パターン）:**

| Stage | 処理内容 | 入力 | 出力 |
|-------|---------|------|------|
| Extract | Claude エクスポート解析 | `extract/input/` | `extract/output/` |
| Transform | Ollama でナレッジ抽出・要約生成 | Extract 出力 | `transform/output/` |
| Load | Markdown ファイル生成 | Transform 出力 | `load/output/` |

**セッション出力先:** `.staging/@session/YYYYMMDD_HHMMSS/import/`

---

### `retry` / `エラーリトライ`

セッション内のエラーファイルを再処理:

```bash
make retry                       # セッション一覧表示
make retry SESSION=20260119_143052   # 指定セッションのリトライ
make retry ACTION=preview SESSION=xxx  # プレビュー
make retry DEBUG=1 SESSION=xxx   # debug モード
```

**セッション参照:** `.staging/@session/YYYYMMDD_HHMMSS/*/phase.json` のエラー情報

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
- **Python スクリプト実行時は必ず venv を使用**: `src/converter/.venv/bin/python` または `make` コマンド
- **レガシーコード (`src/converter/`) は一切修正しない**: 新 ETL パイプライン (`src/etl/`) のみを修正対象とする

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
| `make test` | ユニットテスト + 統合テスト |
| `make test-fixtures` | LLM使用の目視確認テスト |
| `make import` | Claude会話インポート（新） |
| `make organize` | ファイル整理（新） |
| `make status` | セッション状態確認（新） |
| `make retry` | 失敗リトライ（新） |
| `make session-clean` | 古いセッション削除（新） |
| `make llm-import` | Claude会話インポート（レガシー） |
| `make preview` | プレビューモード（レガシー） |

**※ `python -m pytest` 直接実行は統合テストがスキップされるため非推奨**

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+（標準ライブラリ中心） |
| LLM | Ollama API（ローカル） |
| データ形式 | Markdown, JSON, JSONL |
| テスト | unittest（標準ライブラリ） |
| Lint | ruff（オプション） |
| ファイル追跡 | file_id（SHA256ハッシュベース） |

## Active Technologies
- Python 3.11+ + haystack-ai, ollama-haystack, qdrant-haystack (001-rag-migration-plan)
- Qdrant (ローカルファイル永続化 @ `data/qdrant/`) (001-rag-migration-plan)
- Python 3.11+ + tenacity (8.x), ollama (existing) (025-bonobo-tenacity-migration)
- ETL パイプライン: `src/etl/` - tenacity ベースのリトライ、セッション管理 (025-bonobo-tenacity-migration)
- JSON ファイル（session.json, phase.json）、Markdown ファイル (025-bonobo-tenacity-migration)
- Python 3.13（src/etl 既存環境） + tenacity 8.x（既存）、ollama（既存 common/ 経由） (026-etl-import-parity)
- ファイルシステム（JSON, Markdown）、セッションフォルダ構造 (026-etl-import-parity)
- Python 3.13（src/etl 既存環境） + tenacity 8.x（既存）、ollama API（src/etl/utils/ にコピー） (026-etl-import-parity)
- Python 3.13（既存 ETL パイプライン） + tenacity 8.x（既存）、標準ライブラリ（json, pathlib, dataclasses） (027-debug-step-output)
- ファイルシステム（JSONL 形式） (027-debug-step-output)
- Python 3.13（既存 src/etl 環境） + tenacity 8.x（既存）、標準ライブラリ（dataclasses, json, pathlib） (028-flexible-io-ratios)
- ファイルシステム（JSONL, Markdown） (028-flexible-io-ratios)
- Python 3.13（既存 ETL 環境） + tenacity 8.x（既存）、ollama（既存）、zipfile（標準ライブラリ） (030-chatgpt-import)
- ファイルシステム（JSON, JSONL, Markdown） (030-chatgpt-import)
- Python 3.13 + tenacity 8.x, ollama, 標準ライブラリ（json, pathlib, dataclasses） (031-extract-discovery-delegation)
- Python 3.11+ (pyproject.toml: requires-python = ">=3.11") + tenacity 8.x, ollama (既存), 標準ライブラリ (json, pathlib, dataclasses, zipfile) (032-extract-step-refactor)
- ファイルシステム (JSON, JSONL, Markdown) (032-extract-step-refactor)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（既存）、標準ライブラリ（subprocess, pathlib, re, yaml） (034-jekyll-import)
- ファイルシステム（JSON, JSONL, Markdown）- セッションフォルダ構造 (034-jekyll-import)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（既存）、標準ライブラリ（abc, dataclasses, json, pathlib） (035-chunking-mixin)
- Python 3.11+ + argparse (stdlib), pathlib (stdlib) - Modular CLI structure (src/etl/cli/) (036-cli-refactor)
- File system (session JSON files, phase JSON files) - CLI commands in separate modules (036-cli-refactor)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, pathlib, dataclasses） (037-resume-mode-redesign)
- ファイルシステム（JSONL ログ、Markdown ファイル、JSON セッションデータ） (037-resume-mode-redesign)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, dataclasses） (038-too-large-llm-context)
- Python 3.11+ (pyproject.toml: `requires-python = ">=3.11"`) + tenacity 8.x（リトライ）, ollama（LLM API）, 標準ライブラリ（json, dataclasses） (039-resume-baseclass-refactor)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（リトライ）、ollama（LLM API）、PyYAML 6.0+、標準ライブラリ（json, pathlib, dataclasses, abc） (040-resume-extract-reuse)
- ファイルシステム（JSONL, JSON, Markdown）- セッションフォルダ構造 (040-resume-extract-reuse)
- Python 3.11+ (pyproject.toml: `requires-python = ">=3.11"`) + tenacity 8.x（リトライ）、ollama（LLM API）、標準ライブラリ（json, pathlib, dataclasses, zipfile） (041-fix-extract-dedup)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + tenacity 8.x（リトライ）、ollama（LLM API）、標準ライブラリ（re, json, dataclasses） (042-llm-markdown-response)
- Python 3.11+（pyproject.toml: `requires-python = ">=3.11"`） + Kedro 1.1.1, kedro-datasets, tenacity 8.x, PyYAML 6.0+, requests 2.28+ (044-kedro-migration)
- ファイルシステム（JSON, JSONL, Markdown）、Kedro DataCatalog（PartitionedDataset） (044-kedro-migration)

## Recent Changes
- 001-rag-migration-plan: Added Python 3.11+ + haystack-ai, ollama-haystack, qdrant-haystack
