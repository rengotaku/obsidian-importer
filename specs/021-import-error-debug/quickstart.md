# Quickstart: LLMインポート エラーデバッグ改善

## 開発環境セットアップ

```bash
# 仮想環境（既存）
cd development
source .venv/bin/activate

# テスト実行
make test
```

## 実装順序

### Phase 1: エラー詳細出力 (US1)

1. `common/error_writer.py` 作成
   - ErrorDetail データクラス
   - Markdown 出力関数（10MB トランケーション対応）

2. `common/knowledge_extractor.py` 修正
   - ExtractionResult に user_prompt フィールド追加
   - LLM プロンプトを保持

3. `cli.py` 修正
   - エラー時に error_writer 呼び出し

### Phase 2: フォルダ構造変更 (US2)

1. `common/folder_manager.py` 作成
   - セッションフォルダ作成
   - パス解決関数

2. `common/session_logger.py` 修正
   - FolderManager 統合
   - get_paths() メソッド追加
   - parsed/, output/, errors/ サブフォルダ対応

3. `cli.py` 修正
   - Phase 1 出力先: `@plan/import/{session}/parsed/conversations/`
   - Phase 2 出力先: `@plan/import/{session}/output/`
   - エラー出力先: `@plan/import/{session}/errors/`

### Phase 3: 中間ファイル保持 (US3)

1. `cli.py` 修正
   - 中間ファイル削除ロジック削除
   - output/ から @index/ へコピー（削除しない）

2. `session_logger.py` 修正
   - finalize() で intermediate_files を session.json に追加

## 新しいフォルダ構造

```
.staging/@plan/
├── import/{session_id}/
│   ├── parsed/conversations/   # Phase 1 出力
│   ├── output/                 # Phase 2 出力（中間）
│   ├── errors/                 # エラー詳細
│   ├── session.json
│   ├── processed.json
│   ├── errors.json
│   └── results.json
├── organize/{session_id}/
└── test/{session_id}/
```

## テスト方針

```bash
# ユニットテスト
make test

# 統合テスト（LLM使用）
make test-fixtures
```

## 検証手順

1. **エラー詳細出力の確認**
   ```bash
   # インポートを実行
   make llm-import LIMIT=5

   # エラーファイルを確認
   ls .staging/@plan/import/*/errors/
   ```

2. **中間ファイル保持の確認**
   ```bash
   # インポート後
   ls .staging/@plan/import/*/parsed/conversations/
   ls .staging/@plan/import/*/output/

   # session.json の intermediate_files を確認
   cat .staging/@plan/import/*/session.json | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('intermediate_files', {}))"
   ```

3. **@index/ へのコピー確認**
   ```bash
   ls .staging/@index/*.md | head -10
   ```
