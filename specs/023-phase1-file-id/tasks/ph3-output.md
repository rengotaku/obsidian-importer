# Phase 3 完了: User Story 2 - pipeline_stages.jsonl での file_id 記録

## 概要

Phase 3 では、各パイプラインステージの実行ログ（`pipeline_stages.jsonl`）に `file_id` を含める機能を実装した。

## 実行タスク

| タスク | 説明 | 結果 |
|--------|------|------|
| T012 | 前フェーズ出力読み込み | 完了 |
| T013 | `log_stage()` に `file_id` パラメータ追加 | 完了 |
| T014 | `log_stage()` with file_id のテスト追加 | 完了 |
| T015 | `cli.py` Phase 1 で file_id を `log_stage()` に渡す | 完了 |
| T016 | `cli.py` Phase 2 で file_id を `log_stage()` に渡す | 完了 |
| T017 | pipeline_stages.jsonl file_id 記録テスト追加 | 完了 |
| T018 | `make test` で全テストパス確認 | 完了 |
| T019 | Phase 3 出力生成 | 本ファイル |

## 実装内容

### T013: `log_stage()` の変更

**ファイル**: `development/scripts/llm_import/common/session_logger.py`

```python
def log_stage(
    self,
    filename: str,
    stage: str,
    timing_ms: int,
    executed: bool = True,
    skipped_reason: str | None = None,
    before_chars: int | None = None,
    after_chars: int | None = None,
    file_id: str | None = None,  # 新規追加
) -> None:
    """処理ステージを記録する (US2)

    Args:
        ...
        file_id: ファイル追跡用ID（12文字の16進数ハッシュ）

    Side Effects:
        - pipeline_stages.jsonl に追記
    """
    ...
    record = {
        "timestamp": timestamp(),
        "filename": filename,
        "stage": stage,
        "executed": executed,
        "timing_ms": timing_ms,
        "skipped_reason": skipped_reason,
    }

    # file_id（指定された場合のみ）
    if file_id is not None:
        record["file_id"] = file_id
    ...
```

**変更点**:
- `file_id: str | None = None` パラメータを追加（オプショナル）
- `file_id` が指定された場合のみ、record に含める
- 後方互換性を維持（`file_id` なしでも動作）

### T015, T016: `cli.py` の変更

**ファイル**: `development/scripts/llm_import/cli.py`

#### Phase 1 での file_id 渡し (T015)

```python
# T026: log_stage for Phase 1 (T015: file_id を渡す)
phase1_ms = int((time.time() - phase1_start) * 1000)
session_logger.log_stage(
    filename=conv.title,
    stage="phase1",
    timing_ms=phase1_ms,
    executed=True,
    file_id=phase1_file_id,  # 新規追加
)
```

#### Phase 2 での file_id 渡し (T016)

通常処理:
```python
# T026: log_stage for Phase 2 success (T016: file_id を渡す)
session_logger.log_stage(
    filename=conv.title,
    stage="phase2",
    timing_ms=phase2_ms,
    executed=True,
    before_chars=before_chars,
    after_chars=after_chars,
    file_id=document.file_id,  # 新規追加
)
```

チャンク処理時:
```python
# T016: チャンク成功時は最初のチャンクの file_id を使用
first_chunk_file_id = None
for _, result in chunk_results:
    if result.success and result.document:
        first_chunk_file_id = result.document.file_id
        break
session_logger.log_stage(
    filename=conv.title,
    stage="phase2",
    timing_ms=phase2_ms,
    executed=True,
    file_id=first_chunk_file_id,  # 新規追加
)
```

### T014, T017: テストの追加

**ファイル**: `development/scripts/tests/llm_import/test_session_logger.py`

追加テスト:
- `test_log_stage_with_file_id`: file_id が record に含まれることを確認
- `test_log_stage_without_file_id`: file_id なしの場合に含まれないことを確認（後方互換性）

**ファイル**: `development/scripts/llm_import/tests/test_cli.py`

追加テストクラス `TestPipelineStagesFileIdRecording`:
- `test_log_stage_records_file_id_for_phase1`: Phase 1 の log_stage が file_id を記録
- `test_log_stage_records_file_id_for_phase2`: Phase 2 の log_stage が file_id を記録
- `test_backward_compatibility_without_file_id`: file_id なしでも動作（後方互換性）

## テスト結果

```
Ran 241 tests in 0.167s
OK (skipped=1)
```

- normalizer テスト: 123件 OK
- 統合テスト: 6件 OK
- llm_import テスト: 112件 OK（+3件追加）

## 出力例

`pipeline_stages.jsonl` のエントリ:

```json
{"timestamp": "2026-01-18T12:34:56", "filename": "テスト会話", "stage": "phase1", "executed": true, "timing_ms": 100, "skipped_reason": null, "file_id": "a1b2c3d4e5f6"}
{"timestamp": "2026-01-18T12:34:57", "filename": "テスト会話", "stage": "phase2", "executed": true, "timing_ms": 5000, "skipped_reason": null, "file_id": "a1b2c3d4e5f6", "before_chars": 10000, "after_chars": 3000, "diff_ratio": -0.7}
```

## 次フェーズへの引き継ぎ

### 利用可能な機能

1. **`log_stage(file_id=...)`** - file_id 付きのステージログ記録
2. **Phase 1 での file_id 記録** - `cli.py` で Phase 1 実行時に file_id が pipeline_stages.jsonl に記録
3. **Phase 2 での file_id 記録** - `cli.py` で Phase 2 実行時に file_id が pipeline_stages.jsonl に記録

### Phase 4 での作業

1. Phase 2 で parsed ファイルから file_id を読み取る機能の実装
2. Phase 1 と Phase 2 間での file_id 継承の検証

## Checkpoint 確認

pipeline_stages.jsonl に file_id が記録される:
- `log_stage()` が `file_id` パラメータをサポート
- Phase 1, Phase 2 の両方で `file_id` を渡す
- `file_id` フィールドは指定された場合のみ JSONL に含まれる（後方互換性維持）
