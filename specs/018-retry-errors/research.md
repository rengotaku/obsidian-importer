# Research: エラーファイルのリトライ機能

**Date**: 2026-01-17
**Feature**: 018-retry-errors

## 調査項目

### 1. 既存セッション構造の確認

**Question**: セッションディレクトリの構造と errors.json のフォーマットは？

**Findings**:
- セッションディレクトリ: `.staging/@plan/import_YYYYMMDD_HHMMSS/`
- 含まれるファイル:
  - `session.json` - セッションメタデータ
  - `errors.json` - エラーエントリのリスト
  - `processed.json` - 処理済みエントリのリスト
  - `pending.json` - 未処理エントリのリスト
  - `execution.log` - 実行ログ
  - `results.json` - 処理結果サマリー
  - `pipeline_stages.jsonl` - 各ステージの詳細ログ

**errors.json 構造**:
```json
[
  {
    "file": "fe26208b-dc85-48be-a01f-2e8fc98684b8",
    "error": "JSONパースエラー: Invalid \\escape (位置 1166)",
    "stage": "phase2",
    "timestamp": "2026-01-16T21:42:18"
  }
]
```

**Decision**: 既存の errors.json 構造をそのまま利用。`file` フィールドは会話 ID（UUID）。

---

### 2. セッション検出方法

**Question**: エラーを含むセッションをどのように検出するか？

**Findings**:
- `.staging/@plan/import_*` ディレクトリを glob でスキャン
- 各ディレクトリの `errors.json` を読み込み、空でないものを対象
- 更新日時は `session.json` の `updated_at` または `errors.json` の mtime を使用

**Decision**:
- `pathlib.glob("import_*")` でセッションディレクトリを取得
- `errors.json` を読み込んでエラー件数をカウント
- 更新日時でソート（最新順）

---

### 3. Phase 1 出力ファイルの特定

**Question**: エラーの会話 ID から Phase 1 出力ファイルをどのように特定するか？

**Findings**:
- Phase 1 出力は `@index/claude/parsed/conversations/{uuid}.md` に保存
- 既存の `processed.json` には `input_file` と `output_file` のマッピングがある
- しかし errors.json には `file`（会話 ID）のみで、パスは含まれない

**Decision**:
- 会話 ID から Phase 1 出力パスを構築: `@index/claude/parsed/conversations/{uuid}.md`
- ファイルが存在しない場合はスキップしてログに記録

---

### 4. 既存の Phase 2 処理の再利用

**Question**: 既存の `--phase2-only` オプションのロジックを活用できるか？

**Findings**:
- `cli.py` の `process_conversations()` 関数で Phase 1/2 を制御
- `--phase2-only` は Phase 1 をスキップして Phase 2 のみ実行
- `KnowledgeExtractor` クラスが Phase 2 処理を担当

**Decision**:
- 新しい `RetryProcessor` クラスを作成
- 既存の `KnowledgeExtractor` を再利用
- Phase 1 出力ファイルを直接読み込んで Phase 2 に渡す

---

### 5. SessionLogger の拡張

**Question**: リトライセッション用に SessionLogger をどのように拡張するか？

**Findings**:
- `SessionLogger.__init__()` で `prefix` パラメータを受け取る（デフォルト: "import"）
- `start_session()` で session.json を作成
- 現在の session.json には `source_session` フィールドがない

**Decision**:
- `SessionLogger.__init__()` に `source_session` パラメータを追加（オプショナル）
- `start_session()` で session.json に `source_session` を追加
- execution.log のヘッダーにリトライ情報を出力

---

### 6. Makefile ターゲット設計

**Question**: `retry` ターゲットの変数と動作をどのように設計するか？

**Findings**:
- 既存の `llm-import` ターゲットは `ACTION`, `LIMIT` 変数を使用
- `ifeq` ディレクティブで条件分岐

**Decision**:
```makefile
retry:
ifeq ($(ACTION),preview)
	@cd $(BASE_DIR)/development && $(PYTHON) -m scripts.llm_import.cli \
		--provider claude --retry-errors --preview \
		$(if $(SESSION),--session $(SESSION),)
else
	@cd $(BASE_DIR)/development && $(PYTHON) -m scripts.llm_import.cli \
		--provider claude --retry-errors \
		$(if $(SESSION),--session $(SESSION),) \
		$(if $(TIMEOUT),--timeout $(TIMEOUT),)
endif
```

---

## 代替案と却下理由

### 代替案 1: 既存セッションを更新する

**却下理由**: ユーザー要件として「記録は残したい」「新しいセッションを作成」が明示されている。履歴のトレーサビリティが失われる。

### 代替案 2: 専用の retry コマンドを作成

**却下理由**: 既存の cli.py を拡張する方がコードの重複を避けられる。argparse の引数追加で十分対応可能。

### 代替案 3: errors.json を直接編集

**却下理由**: データの整合性が崩れるリスク。元のセッションを変更しないことで、問題発生時のデバッグが容易。

---

## 未解決事項

なし - すべての技術的な疑問点が解決済み。
