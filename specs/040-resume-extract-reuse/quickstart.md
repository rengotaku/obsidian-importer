# Quickstart: Resume モード Extract Output 再利用

**Date**: 2026-01-28
**Feature**: 040-resume-extract-reuse

## Prerequisites

- Python 3.11+
- 既存の ETL パイプライン（src/etl/）
- セッションフォルダ構造（.staging/@session/）

## Quick Test

### 1. 新規セッションでインポート実行

```bash
# 新規セッションでインポート（Extract output が生成される）
make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude LIMIT=5
```

### 2. Extract Output の確認

```bash
# Extract output フォルダを確認
ls -la .staging/@session/*/import/extract/output/

# 新しいファイル名パターン: data-dump-0001.jsonl
# ※ 1000 レコード超の場合: data-dump-0002.jsonl, ...
```

### 3. Resume モードで再実行

```bash
# セッション ID を確認
make status ALL=1

# Resume モードで再実行
make import SESSION=20260128_XXXXXX
```

**期待される動作**:
- 標準出力: `Resume mode: Loading from extract/output/*.jsonl`
- Extract stage は input から再処理されない
- pipeline_stages.jsonl に新しい Extract ログは追記されない

### 4. 重複ログの確認

```bash
# Extract ログの件数を確認（Resume 前後で変わらないこと）
grep '"stage":"extract"' .staging/@session/20260128_XXXXXX/import/pipeline_stages.jsonl | wc -l
```

## Usage Examples

### 新規 Phase クラスの作成

BasePhaseOrchestrator を継承して新規 Phase を作成する例：

```python
from src.etl.core.phase_orchestrator import BasePhaseOrchestrator


class CustomPhase(BasePhaseOrchestrator):
    """カスタム Phase（Resume 機能は自動で動作）"""

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.CUSTOM  # 新規 PhaseType を定義

    def _run_extract_stage(
        self,
        phase_data: Phase,
        debug_mode: bool,
        limit: int | None,
        session_manager,
    ) -> list[ProcessingItem]:
        """Extract stage の具体的な実装"""
        # 独自の Extractor を使用
        extractor = CustomExtractor()
        extract_data = phase_data.stages[StageType.EXTRACT]

        items = extractor.discover_items(extract_data.input_path)

        ctx = StageContext(
            phase=phase_data,
            stage=extract_data,
            debug_mode=debug_mode,
        )
        return list(extractor.run(ctx, items))

    def _run_transform_stage(
        self,
        phase_data: Phase,
        items: list[ProcessingItem],
        debug_mode: bool,
        limit: int | None,
        completed_cache: CompletedItemsCache | None,
    ) -> Iterator[ProcessingItem]:
        """Transform stage の具体的な実装"""
        transformer = CustomTransformer()
        transform_data = phase_data.stages[StageType.TRANSFORM]

        ctx = StageContext(
            phase=phase_data,
            stage=transform_data,
            debug_mode=debug_mode,
            completed_cache=completed_cache,  # FW が渡す
        )
        return transformer.run(ctx, items)

    def _run_load_stage(
        self,
        phase_data: Phase,
        items: Iterator[ProcessingItem],
        debug_mode: bool,
        completed_cache: CompletedItemsCache | None,
    ) -> Iterator[ProcessingItem]:
        """Load stage の具体的な実装"""
        loader = CustomLoader()
        load_data = phase_data.stages[StageType.LOAD]

        ctx = StageContext(
            phase=phase_data,
            stage=load_data,
            debug_mode=debug_mode,
            completed_cache=completed_cache,  # FW が渡す
        )
        return loader.run(ctx, items)
```

**ポイント**:
- `run()` メソッドは実装不要（FW が提供）
- フックメソッド 3 つ（`_run_extract_stage`, `_run_transform_stage`, `_run_load_stage`）のみ実装
- Resume ロジックは FW が自動的に処理

## Verification

### テスト実行

```bash
# 全テスト実行
make test

# 特定のテストファイル
python -m unittest src/etl/tests/test_phase_orchestrator.py
python -m unittest src/etl/tests/test_resume_mode.py
```

### 手動検証

1. **Extract output のファイル名パターン**:
   - `data-dump-0001.jsonl` 形式であること
   - 1000 レコード超で `data-dump-0002.jsonl` が生成されること

2. **Resume モードの動作**:
   - `Resume mode: Loading from extract/output/*.jsonl` が表示されること
   - pipeline_stages.jsonl に Extract ログが追記されないこと

3. **既存機能の互換性**:
   - ImportPhase が正常に動作すること
   - OrganizePhase が正常に動作すること
   - 既存のテストがすべてパスすること

## Troubleshooting

### Q: Resume モードで「Extract output not found」が表示される

**原因**: extract/output/ フォルダに data-dump-*.jsonl が存在しない

**解決策**:
1. 新規セッションでインポートを完了させる
2. または、--session オプションを確認する

### Q: Resume 後もログが重複する

**原因**: 旧形式のファイル名（source_path.stem ベース）が存在する

**解決策**:
1. extract/output/ 内の古い JSONL ファイルを削除
2. 新規セッションで再実行

### Q: 新規 Phase で Resume が動作しない

**原因**: BasePhaseOrchestrator を継承していない

**解決策**:
1. Phase クラスが BasePhaseOrchestrator を継承していることを確認
2. フックメソッドが正しく実装されていることを確認
