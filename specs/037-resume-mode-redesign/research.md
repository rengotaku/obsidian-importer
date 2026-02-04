# Research: Resume モードの再設計

## 1. 現在のアーキテクチャ分析

### 1.1 パイプライン構造

```
ImportPhase.run()
  ├── Extract Stage (discover_items → run)
  ├── Transform Stage (run)
  └── Load Stage (run)
```

**現在のログ出力**: `BaseStage._write_jsonl_log()` が各アイテム処理後に `pipeline_stages.jsonl` へ追記。

### 1.2 現在の問題点

| 問題 | 詳細 |
|------|------|
| スキップ判定なし | 現在の `BaseStage.run()` は全アイテムを処理 |
| DEBUG モード依存 | ログ出力が debug_mode に依存 |
| ステージ別戦略なし | Extract/Transform/Load が同じ処理フロー |

### 1.3 既存の処理済みアイテム追跡

現在 `pipeline_stages.jsonl` には以下の情報が記録されている:
- `item_id`: アイテムの一意識別子
- `parent_item_id`: チャンク分割時の親アイテム ID
- `status`: "success" / "failed" / "skipped"
- `stage`: "extract" / "transform" / "load"

## 2. 設計決定

### 2.1 スキップ判定の責務配置

**Decision**: フレームワーク層（BaseStage/Phase）に配置

**Rationale**:
- 具象 Step クラスは処理ロジックのみに集中
- Resume モードの知識が Step に漏れない
- 一貫したスキップ判定ロジック

**Alternatives considered**:
1. Step クラスにスキップ判定を委譲 → ❌ 各 Step が Resume を意識する必要がある
2. CLI 層でフィルタリング → ❌ パイプライン内部の状態管理と乖離

### 2.2 ステージ別スキップ戦略

**Decision**: FR-003〜FR-005 に従ったステージ別戦略

| ステージ | スキップ単位 | 判定方法 | 理由 |
|---------|------------|---------|------|
| Extract | Stage 単位 | `extract/output/` にファイルが存在 | 軽量処理（ファイル読み込み、JSON パース） |
| Transform | アイテム単位 | `pipeline_stages.jsonl` の status="success" | LLM 呼び出し（コスト大） |
| Load | アイテム単位 | `pipeline_stages.jsonl` の status="success" | 冪等性あるが効率化のため |

**Rationale**:
- Transform の LLM 呼び出しがコストの大部分を占める
- Extract は再実行しても数秒で完了
- Load は冪等だが、不要な I/O を避ける

### 2.3 DEBUG モード廃止

**Decision**: `--debug` フラグを削除し、詳細ログ出力を通常動作に昇格

**Rationale**:
- Resume モードにログが必須
- ログなしでは処理済みアイテムの判定ができない
- ログファイルサイズは許容範囲（数千〜数万レコード）

**Alternatives considered**:
1. DEBUG モードのみでログ出力 → ❌ Resume モードが DEBUG 必須になる
2. 別のログファイルを用意 → ❌ 複雑化、整合性の問題

### 2.4 スキップアイテムのログ記録

**Decision**: スキップしたアイテムは `pipeline_stages.jsonl` に記録しない（FR-007）

**Rationale**:
- ログの肥大化防止
- Resume 実行ごとにスキップログが追記されると、同じアイテムが複数回記録される
- 統計計算は「入力数 - (成功数 + 失敗数)」で算出可能

**Alternatives considered**:
1. スキップも記録 → ❌ ログ肥大化、重複エントリ
2. 別ファイルに記録 → ❌ 管理の複雑化

### 2.5 チャンク分割アイテムの扱い

**Decision**: `parent_item_id` で元の会話を追跡（FR-011）

**Rationale**:
- チャンク分割されたアイテムは item_id が異なる
- 全チャンクが成功した場合のみ「成功」とみなす
- `parent_item_id` で関連付けることでトレースが可能

**実装方針**:
```python
# チャンク分割アイテムの成功判定
def is_chunked_item_completed(item_id: str, completed_items: set[str]) -> bool:
    # 単純なケース: item_id がそのまま完了リストにある
    if item_id in completed_items:
        return True
    # チャンクされたアイテムは個別にチェック（pipeline_stages.jsonl を参照）
    return False
```

## 3. 実装アプローチ

### 3.1 CompletedItemsCache

```python
@dataclass
class CompletedItemsCache:
    """処理完了アイテムのキャッシュ。"""

    items: set[str]
    """成功した item_id のセット。"""

    @classmethod
    def from_jsonl(cls, jsonl_path: Path, stage: StageType) -> "CompletedItemsCache":
        """pipeline_stages.jsonl から処理完了アイテムを読み込む。"""
        items = set()
        if jsonl_path.exists():
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if record.get("stage") == stage.value and record.get("status") == "success":
                        item_id = record.get("item_id")
                        if item_id:
                            items.add(item_id)
        return cls(items=items)
```

### 3.2 BaseStage.run() の修正

```python
def run(self, ctx: StageContext, items: Iterator[ProcessingItem]) -> Iterator[ProcessingItem]:
    # Resume モード: 処理完了アイテムを読み込み
    completed_cache = CompletedItemsCache.from_jsonl(
        ctx.phase.pipeline_stages_jsonl,
        self.stage_type,
    )

    for item in items:
        # スキップ判定
        if item.item_id in completed_cache.items:
            ctx.skip_count += 1
            continue  # ログには記録せず、次のアイテムへ

        # 通常処理
        # ...（既存のロジック）
```

### 3.3 Extract Stage の Stage 単位スキップ

```python
# ImportPhase.run() 内
extract_output = phase_data.stages[StageType.EXTRACT].output_path
if extract_output.exists() and any(extract_output.iterdir()):
    # Extract 済み: Transform から開始
    items = self._load_extracted_items(extract_output)
else:
    # 新規: Extract から開始
    items = extract_stage.discover_items(input_path)
    items = extract_stage.run(extract_ctx, items)
```

## 4. テスト戦略

### 4.1 ユニットテスト

| テストケース | 検証内容 |
|------------|---------|
| `test_completed_items_cache_empty` | 空のログファイルで空のキャッシュを返す |
| `test_completed_items_cache_with_success` | 成功アイテムがキャッシュに含まれる |
| `test_completed_items_cache_ignores_failed` | 失敗アイテムはキャッシュに含まれない |
| `test_skip_completed_item` | 処理完了アイテムがスキップされる |
| `test_skip_not_logged` | スキップアイテムがログに記録されない |

### 4.2 統合テスト

| テストケース | 検証内容 |
|------------|---------|
| `test_resume_after_partial_completion` | 部分完了後の Resume で未処理のみ処理 |
| `test_resume_after_crash` | クラッシュ後の Resume で中断箇所から再開 |
| `test_no_duplicate_llm_calls` | LLM 呼び出しの重複がない |

## 5. 移行計画

### 5.1 後方互換性

- 既存の `pipeline_stages.jsonl` は変更なしで読み込み可能
- `--debug` フラグは警告を出力後、無視（deprecated）
- `debug_mode` パラメータは内部的に無視

### 5.2 段階的移行

1. **Phase 1**: CompletedItemsCache の実装とテスト
2. **Phase 2**: Transform/Load ステージのアイテム単位スキップ
3. **Phase 3**: Extract ステージの Stage 単位スキップ
4. **Phase 4**: DEBUG モード廃止、CLI フラグ削除
5. **Phase 5**: 統合テスト、ドキュメント更新

## 6. パフォーマンス考慮

### 6.1 ログファイル読み込み

**要件**: 1000件のログ読み込みが1秒以内（SC-003）

**実装**:
- JSONL 形式で行単位読み込み
- set に変換（O(1) ルックアップ）
- 1回の読み込みで全ステージの完了アイテムをキャッシュ

**見積もり**:
- 1レコード ≈ 500バイト
- 1000レコード ≈ 500KB
- 読み込み + パース: <100ms

### 6.2 メモリ使用量

- item_id は UUID 形式（36文字）
- 10000件 × 36バイト ≈ 360KB
- 許容範囲内
