# Research: Resume モード Extract Output 再利用

**Date**: 2026-01-28
**Feature**: 040-resume-extract-reuse

## Research Tasks

### 1. 既存の Extract Output 書き込み実装

**調査対象**: `BaseStage._write_output_item()` メソッド（src/etl/core/stage.py:803-826）

**現状**:
```python
def _write_output_item(self, ctx: StageContext, item: ProcessingItem) -> None:
    # Generate output filename
    safe_name = item.source_path.stem.replace("/", "_").replace("\\", "_")
    output_file = ctx.output_path / f"{safe_name}.jsonl"

    # Write item as JSONL (one line per item)
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(item_dict, ensure_ascii=False) + "\n")
```

**問題点**:
- ファイル名が `source_path.stem` に依存し、可変的
- Resume 時に特定のパターンでファイルを検索しにくい
- ファイルサイズの分割機能がない

**Decision**: 固定ファイル名パターン `data-dump-{番号4桁}.jsonl` に変更し、1000 レコードごとに分割

**Rationale**:
- Resume 時に `data-dump-*.jsonl` パターンで確実にファイルを特定できる
- 分割によりファイル肥大化を防止
- Git 差分が小さくなる（既存ファイルは変更されない）

**Alternatives considered**:
- 単一ファイル維持: 大規模セッションで肥大化
- UUID ベースファイル名: Resume 時の特定が困難

### 2. ImportPhase.run() の Resume ロジック

**調査対象**: `ImportPhase.run()` メソッド（src/etl/phases/import_phase.py:115-303）

**現状**:
- Resume モードでも `extract_stage.discover_items()` → `extract_stage.run()` を実行
- Extract の output が存在しても input から再処理される
- `pipeline_stages.jsonl` に Extract ログが重複記録される

**問題のコードフロー**:
```python
# Discover items - delegate to extract_stage
items = extract_stage.discover_items(input_path, chunk=self._chunk)

# Run Extract stage
extract_ctx = StageContext(...)
extracted_iter = extract_stage.run(extract_ctx, items)  # ← 毎回実行
extracted = list(extracted_iter)
```

**Decision**: BasePhaseOrchestrator で Extract output の存在を確認し、存在する場合は JSONL から ProcessingItem を復元

**Rationale**:
- Extract stage の run() をスキップすることで、ログの重複を防止
- FW レベルで制御することで、各 Phase での実装漏れを防止
- Transform/Load は既存の completed_cache 機構で対応済み

**Alternatives considered**:
- Extract stage に completed_cache を追加: discover_items() が毎回実行されるため根本解決にならない
- JSONL ログを重複チェック: 計算コストが高く、根本解決にならない

### 3. ProcessingItem のシリアライズ/デシリアライズ

**調査対象**: `ProcessingItem.to_dict()` と `ProcessingItem.from_dict()`

**現状**:
- `to_dict()`: すべてのフィールドを辞書に変換
- `from_dict()`: 辞書から ProcessingItem を復元

**検証結果**: 既存の実装で Resume に必要な情報（item_id, source_path, status, metadata, content 等）が完全にシリアライズ/デシリアライズされる

**Decision**: 既存の `ProcessingItem.from_dict()` を使用

**Rationale**: 追加実装不要、既存の JSONL 形式と互換性あり

### 4. Template Method パターンの適用

**調査対象**: Python での Template Method パターン実装

**Best Practices**:
- ABC（Abstract Base Class）を使用
- 制御フローを持つ `run()` メソッドを concrete として実装
- フックメソッドを abstract として定義
- protected メソッドには `_` プレフィックス

**Decision**: BasePhaseOrchestrator を ABC として実装、`run()` を concrete、`_run_extract_stage()` 等を abstract に

**Rationale**:
- Python の標準的なパターン
- 既存の BaseStage と同様のアプローチ
- IDE でのサポートが良い

### 5. ファイル分割のレコード数

**調査対象**: JSONL ファイルの適切なサイズ

**考慮事項**:
- ProcessingItem 1 件あたり約 10KB（会話の長さによる）
- 1000 レコード × 10KB = 約 10MB/ファイル
- Git でのハンドリング: 10MB 以下が推奨
- 読み込み効率: 小さいファイルの方が効率的

**Decision**: 1000 レコード/ファイル

**Rationale**:
- 10MB 程度に収まり、Git に優しい
- Resume 時の読み込みが効率的
- 既存セッション（848 件）では 1 ファイルで収まる

**Alternatives considered**:
- 500 レコード: ファイル数が増えすぎる
- 2000 レコード: ファイルサイズが大きくなりすぎる

## Summary

| 項目 | Decision |
|------|----------|
| ファイル名 | `data-dump-{番号4桁}.jsonl` |
| 分割単位 | 1000 レコード |
| FW パターン | Template Method (BasePhaseOrchestrator) |
| Resume 検出 | `data-dump-*.jsonl` の存在確認 |
| シリアライズ | 既存の ProcessingItem.to_dict()/from_dict() |

## NEEDS CLARIFICATION Resolution

Technical Context に NEEDS CLARIFICATION はなし。すべての技術的決定が完了。
