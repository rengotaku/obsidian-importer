# Research: ChatGPTExtractor Steps分離リファクタリング

**Date**: 2026-01-24
**Status**: Complete

## Research Topics

### 1. 既存の 1:N 展開パターン

**Question**: 既存コードベースに 1:N 展開パターンはあるか？

**Findings**:
- **ClaudeExtractor** は `_expand_conversations()` で 1:N 展開を実行
- しかしこれは `discover_items()` 内で行われ、Step 機構は使用していない
- 両 Extractor とも `discover_items()` 内で展開処理を完結

**Code Evidence**:
```python
# ClaudeExtractor._expand_conversations() (line 209-284)
for conv in conversations:
    # ... 1:N 展開ロジック
    yield ProcessingItem(...)
```

**Decision**: 既存パターンを参考にしつつ、Step 機構に統合する新設計が必要

---

### 2. BaseStep の現在のインターフェース

**Question**: BaseStep は 1:1 処理のみをサポートするか？

**Findings**:
- `BaseStep.process()` は `ProcessingItem -> ProcessingItem` の 1:1 シグネチャ
- `BaseStage._process_item()` は単一アイテムを順次処理
- `BaseStage.run()` は items イテレータを受け取り、各アイテムを個別処理

**Code Evidence**:
```python
# BaseStep (core/stage.py line 181-194)
@abstractmethod
def process(self, item: ProcessingItem) -> ProcessingItem:
    """Process a single item."""
    ...
```

**Decision**: 1:N 展開には新しい Step タイプ（ExpandingStep）が必要

---

### 3. steps.jsonl 出力メカニズム

**Question**: steps.jsonl はどのタイミングで出力されるか？

**Findings**:
- `_write_debug_step_output()` は各 Step 処理後に呼び出される
- `_process_item()` 内でループごとに呼び出し
- DEBUG モードでのみ出力

**Code Evidence**:
```python
# BaseStage._process_item() (line 360-371)
self._write_debug_step_output(
    ctx,
    current,
    step_index,
    step.name,
    timing_ms=timing_ms,
    before_chars=before_chars,
    after_chars=after_chars,
)
```

**Decision**: 1:N 展開 Step でも同じメカニズムを使用し、展開前後のログを記録

---

### 4. ProcessingItem の親子関係追跡

**Question**: 展開されたアイテムの親子関係をどう追跡するか？

**Findings**:
- 既存の chunking 機能で `parent_item_id` メタデータを使用
- `is_chunked`, `chunk_index`, `total_chunks` も定義済み

**Code Evidence**:
```python
# ProcessingItem docstring (models.py line 142-149)
Metadata Schema for Chunked Items:
    - is_chunked (bool): True if this item was created from chunk splitting
    - chunk_index (int): 0-based chunk index (0, 1, 2, ...)
    - total_chunks (int): Total number of chunks created from parent
    - parent_item_id (str): Original item ID before chunking
```

**Decision**: 同様のパターンを 1:N 展開に適用。`parent_item_id` で展開元を追跡

---

### 5. 汎用 1:N Step の設計アプローチ

**Question**: Extract/Transform 両方で使える汎用設計は？

**Findings**:
- **Option A**: 新しい基底クラス `ExpandingStep` を追加
  - `process()` を `Iterator[ProcessingItem]` を返すように変更
  - `BaseStage._process_item()` で型チェックして分岐
- **Option B**: `process()` の戻り値を `ProcessingItem | list[ProcessingItem]` に
  - 既存コードとの互換性維持しやすい
  - 型ヒントは Union で対応
- **Option C**: `expand()` メソッドを追加し、オプショナルに
  - `expand()` が定義されていれば 1:N、なければ 1:1

**Decision**: **Option B** を採用
- 理由: 最小限の変更で後方互換性を維持
- `process()` が list を返した場合のみ 1:N 展開として処理
- 既存の Step は変更不要（単一 ProcessingItem を返し続ける）

---

### 6. ChatGPT フォーマット変換の分離

**Question**: discover_items() のどの処理を Step に分離するか？

**Findings** (spec.md Data Flow セクションより):
1. **ReadZipStep** (1:1): ZIP → conversations.json 抽出
2. **ParseConversationsStep** (1:N): JSON → N 個の conversation dict
3. **ConvertFormatStep** (1:1): ChatGPT mapping → Claude messages
4. **ValidateMinMessagesStep** (1:1): MIN_MESSAGES チェック

**Decision**: 4つの Step に分離。Step 2 のみが 1:N 展開

---

### 7. session.json フェーズ統計の設計

**Question**: 各フェーズ完了時の item 数をどう記録するか？

**Findings**:
- 現在の `Session.phases` は `list[str]` で、フェーズ名のみを記録
- Phase クラスには既に `success_count`, `error_count` フィールドが存在
- CLI で phase 完了後に `session.phases.append("import")` のように追加

**Options**:
- **Option A**: `phases` を `dict[str, dict]` に変更（フェーズ名 → 統計）
- **Option B**: 別フィールド `phase_stats` を追加
- **Option C**: Phase.json から読み込む（session.json は変更なし）

**Decision**: **Option A** を採用
- 理由: 最もシンプルで、session.json 単体で統計を確認可能
- `PhaseStats` dataclass を追加し、型安全性を確保
- 旧形式（list）との後方互換性を `from_dict()` で維持
- 例外発生時は `status: "crashed"` と `error` フィールドで記録（try/except で捕捉）

---

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| 1:N Step 設計 | `process()` 戻り値を `ProcessingItem \| list[ProcessingItem]` に | 後方互換性維持、最小変更 |
| 親子追跡 | `parent_item_id` メタデータ | 既存 chunking パターンと統一 |
| Step 分離 | 4 Steps (Read, Parse, Convert, Validate) | 責務明確化、テスト容易性 |
| discover_items() | ZIP 発見のみ、content=None | Claude Extractor と統一 |
| session.json phases | `list[str]` → `dict[str, PhaseStats]` | session.json 単体で統計確認可能 |

## Alternatives Considered

### 1:N Step 設計の代替案

| Alternative | Rejected Because |
|-------------|------------------|
| ExpandingStep 基底クラス | 新規クラス追加でコード複雑化 |
| expand() オプショナルメソッド | 2つのコードパスで保守性低下 |
| Generator yield | BaseStage.run() の大幅変更が必要 |

### ProcessingItem 変更の代替案

| Alternative | Rejected Because |
|-------------|------------------|
| 新フィールド `expanded_from` 追加 | metadata で十分、スキーマ変更不要 |
| 子アイテムを `children` リストに格納 | パイプライン処理モデルと不整合 |

### Session.phases 変更の代替案

| Alternative | Rejected Because |
|-------------|------------------|
| 別フィールド `phase_stats` を追加 | `phases` と `phase_stats` の二重管理が必要 |
| Phase.json から読み込み | session.json 単体で統計確認不可、複数ファイル参照が必要 |
