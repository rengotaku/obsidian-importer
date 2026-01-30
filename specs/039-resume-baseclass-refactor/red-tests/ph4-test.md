# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - Resume前提条件チェックと進捗表示
- FAIL テスト数: 2
- テストファイル: src/etl/tests/test_import_phase.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| src/etl/tests/test_import_phase.py | test_resume_requires_extract_complete | Extract stageが未完了の場合、RuntimeErrorを発生させて終了 |
| src/etl/tests/test_import_phase.py | test_resume_shows_progress_message | Resume開始時に「Resume mode: 7/10 items already completed」のような進捗メッセージを表示 |

## テスト詳細

### Test 1: test_resume_requires_extract_complete (T042)

**目的**: Resume mode で Extract stage が完了していない場合、エラーメッセージを表示して終了する

**テストシナリオ**:
1. セッションとフェーズを作成
2. extract/output/ フォルダは存在するがファイルなし（Extract未完了状態）
3. pipeline_stages.jsonl を空ファイルで作成
4. ImportPhase を base_path 付きで初期化（Resume mode）
5. run() 呼び出し時に RuntimeError が発生することを確認
6. エラーメッセージに "Extract stage not completed" が含まれることを確認

**期待するエラーメッセージ**: `"Error: Extract stage not completed. Cannot resume."`

**現在の動作**: RuntimeError は発生せず、テストが FAIL

### Test 2: test_resume_shows_progress_message (T043)

**目的**: Resume mode 開始時に処理済み件数と処理開始位置を標準出力に表示する

**テストシナリオ**:
1. セッションとフェーズを作成
2. extract/output/ に 10 個のファイルを作成（Extract完了状態）
3. session.json に `expected_total_item_count=10` を設定
4. pipeline_stages.jsonl に 7 件の `status="success"` レコードを書き込み
5. ImportPhase を base_path 付きで初期化（Resume mode）
6. stdout をキャプチャして run() を呼び出し
7. 出力に `"Resume mode:"`, `"7"`, `"10"` が含まれることを確認

**期待する出力例**: `"Resume mode: 7/10 items already completed, starting from item 8"`

**現在の動作**: 進捗メッセージは出力されず、stdout は空

## 実装ヒント

### Import Phase での実装場所

`src/etl/phases/import_phase.py` の `run()` メソッド内で以下を追加：

#### 1. Extract完了チェック（run() の最初に追加）

```python
def run(self, phase_data, debug_mode=False, limit=None, session_manager=None):
    # Resume mode check: Extract stage must be completed
    if self.base_path is not None:
        extract_output = phase_data.stages[StageType.EXTRACT].output_path
        if not extract_output.exists() or not any(extract_output.iterdir()):
            raise RuntimeError("Error: Extract stage not completed. Cannot resume.")
```

**チェック条件**:
- `self.base_path` が設定されている（Resume mode）
- `extract/output/` フォルダにファイルが存在すること

#### 2. Resume進捗表示（Extract完了チェック後に追加）

```python
    # Resume mode: Display progress message
    if self.base_path is not None and session_manager is not None:
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
                        if record.get("status") == "success" and record.get("stage") == "transform":
                            completed_count += 1
                    except json.JSONDecodeError:
                        continue

        # Display progress message
        print(f"Resume mode: {completed_count}/{expected_total} items already completed, starting from item {completed_count + 1}")
```

**データ取得**:
- 全体 item 数: `session.json` の `phases["import"].expected_total_item_count`
- 処理完了数: `pipeline_stages.jsonl` から `stage="transform"` かつ `status="success"` をカウント

## FAIL 出力例

```
FAIL: test_resume_requires_extract_complete (src.etl.tests.test_import_phase.TestResumePrerequisites)
T042: Resume mode requires Extract stage to be completed.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_import_phase.py", line 1315, in test_resume_requires_extract_complete
    with self.assertRaises(RuntimeError) as context:
AssertionError: RuntimeError not raised

======================================================================
FAIL: test_resume_shows_progress_message (src.etl.tests.test_import_phase.TestResumePrerequisites)
T043: Resume mode shows progress message at startup.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/project/src/etl/tests/test_import_phase.py", line 1401, in test_resume_shows_progress_message
    self.assertIn(
        "Resume mode:",
        output,
        "Should print 'Resume mode:' prefix",
    )
AssertionError: 'Resume mode:' not found in '' : Should print 'Resume mode:' prefix

----------------------------------------------------------------------
Ran 2 tests in 0.005s

FAILED (failures=2)
```

## 関連ファイル

| ファイル | 役割 |
|----------|------|
| src/etl/phases/import_phase.py | 実装対象（run() メソッド） |
| src/etl/core/session.py | PhaseStats.expected_total_item_count |
| src/etl/core/models.py | CompletedItemsCache（参考実装） |
| src/etl/tests/test_import_phase.py | テストファイル |

## 次ステップ

phase-executor が以下を実行:
1. 「実装 (GREEN)」: ImportPhase.run() に前提条件チェックと進捗表示を追加
2. 「検証」: `make test` で 2 つのテストが PASS することを確認
