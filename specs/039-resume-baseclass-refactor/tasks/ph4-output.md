# Phase 4 Output

## 作業概要
- Phase 4 - Resume前提条件チェックと進捗表示 の実装完了
- FAIL テスト 2 件を PASS させた

## 修正ファイル一覧
- `src/etl/phases/import_phase.py` - Resume前提条件チェックと進捗表示を追加

## 実装の詳細

### T047: Extract完了チェック

`ImportPhase.run()` メソッドの最初に以下のチェックを追加:

```python
# Resume mode check: Extract stage must be completed
if self.base_path is not None:
    extract_output = phase_data.stages[StageType.EXTRACT].output_path
    if not extract_output.exists() or not any(extract_output.iterdir()):
        raise RuntimeError("Error: Extract stage not completed. Cannot resume.")
```

**チェック内容**:
- Resume mode (`self.base_path` が設定されている) の場合のみチェック
- `extract/output/` フォルダが存在すること
- `extract/output/` に少なくとも1つのファイルが存在すること

**エラーメッセージ**: `"Error: Extract stage not completed. Cannot resume."`

これにより、Extract stage が未完了の状態で Resume を試みた場合、早期にエラーで終了し、ユーザーに適切なフィードバックを提供できる。

### T048: Resume進捗表示

Extract完了チェックの直後に、Resume mode 開始時の進捗表示を追加:

```python
# Resume mode: Display progress message
if self.base_path is not None and session_manager is not None:
    import json

    # Get expected total from session.json
    session_id = phase_data.base_path.parent.name
    session = session_manager.load(session_id)
    phase_stats = session.phases.get("import")
    expected_total = phase_stats.expected_total_item_count if phase_stats else 0

    # Count completed items from pipeline_stages.jsonl
    jsonl_path = phase_data.base_path / "pipeline_stages.jsonl"
    completed_count = 0
    if jsonl_path.exists():
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if (
                        record.get("status") == "success"
                        and record.get("stage") == "transform"
                    ):
                        completed_count += 1
                except json.JSONDecodeError:
                    continue

    # Display progress message
    print(
        f"Resume mode: {completed_count}/{expected_total} items already completed, starting from item {completed_count + 1}"
    )
```

**データ取得**:
- 全体 item 数: `session.json` の `phases["import"].expected_total_item_count`
- 処理完了数: `pipeline_stages.jsonl` から `stage="transform"` かつ `status="success"` をカウント

**表示例**:
```
Resume mode: 700/1000 items already completed, starting from item 701
```

これにより、ユーザーは Resume mode 開始時に以下の情報を即座に把握できる:
- すでに処理済みのアイテム数
- 全体のアイテム数
- どこから処理が再開されるか

## テスト結果

### Phase 4 Tests
```
test_resume_requires_extract_complete ... ok
test_resume_shows_progress_message ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.005s

OK
```

**test_resume_requires_extract_complete (T042)**:
- Extract stage が未完了（`extract/output/` にファイルなし）の場合、RuntimeError が発生することを確認
- エラーメッセージに "Extract stage not completed" が含まれることを確認

**test_resume_shows_progress_message (T043)**:
- Resume mode 開始時に進捗メッセージが標準出力に表示されることを確認
- メッセージに "Resume mode:", "7" (completed), "10" (total) が含まれることを確認

### Coverage
Phase 4 で追加したコードは、上記の2つのユニットテストで完全にカバーされている。

## 注意点

### 次 Phase で必要な情報
- Phase 5 (Polish) では、以下を実施:
  - CLAUDE.md の Active Technologies セクション更新
  - quickstart.md の検証シナリオ実行
  - 全エッジケースの検証

### 実装の特徴
- **Early return**: Extract未完了の場合、処理を開始せずに即座にエラー終了
- **ユーザー体験向上**: Resume開始時に進捗を表示することで、処理状況が可視化される
- **破損データ対応**: `pipeline_stages.jsonl` の JSON デコードエラーは無視して処理継続（破損行をスキップ）

### エラーハンドリング
- `pipeline_stages.jsonl` が存在しない場合: `completed_count = 0` として処理継続
- JSON デコードエラー: `try-except` でキャッチし、その行をスキップして次の行へ
- `expected_total_item_count` が未設定の場合: `expected_total = 0` として処理継続

## 実装のミス・課題

特になし。実装は仕様通りに完了し、すべてのテストがパスしている。
