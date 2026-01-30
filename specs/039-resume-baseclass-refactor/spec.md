# Feature Specification: Resume機能の基底クラス集約リファクタリング

**Feature Branch**: `039-resume-baseclass-refactor`
**Created**: 2026-01-27
**Status**: Draft
**Input**: User description: "resume機能が正しく動くように再設計する。基底クラスに機能を集約する。継承クラスはresumeを意識しない作り。"

## ユーザーシナリオ & テスト *(必須)*

### ユーザーストーリー 1 - 中断からの再開（Resume Mode） (Priority: P1)

ETLパイプライン実行中に強制終了（Ctrl+C、システムクラッシュ等）が発生した場合、ユーザーは処理済みアイテムをスキップして未処理アイテムのみ処理を再開できる。

**このプライオリティの理由**: Resume機能はLLM呼び出しのコスト（時間・API料金）を削減する中核機能。処理済みアイテムの再処理を防ぐことで、ユーザーの時間とリソースを節約する。

**独立テスト**: 10件のアイテムを処理中に5件目で強制終了し、再開時に6件目から処理が開始されることを確認。

**受け入れシナリオ**:

1. **Given** Transform stageで5件処理済みの状態, **When** `--session` オプションで再実行, **Then** 5件はスキップされ6件目以降のみ処理される
2. **Given** Load stageで3件処理済みの状態, **When** `--session` オプションで再実行, **Then** 3件はスキップされ4件目以降のみ処理される
3. **Given** Extract stage完了・Transform stage未着手の状態, **When** `--session` オプションで再実行, **Then** Extract stageはスキップされ、Transform stageから処理開始

---

### ユーザーストーリー 2 - 継承クラスの実装簡素化 (Priority: P2)

開発者が新しいExtractor/Transformer/Loaderを実装する際、Resume機能を意識せずに実装できる。

**このプライオリティの理由**: メンテナンス性向上。新規Stage実装時の認知負荷を軽減し、バグの混入を防ぐ。

**独立テスト**: 新規のStage実装で`run_with_skip()`メソッドなしでResume機能が動作することを確認。

**受け入れシナリオ**:

1. **Given** BaseStageを継承した新規Stage, **When** steps プロパティのみ実装, **Then** Resume機能が自動で適用される
2. **Given** 既存のKnowledgeTransformer, **When** run_with_skip()を削除, **Then** 動作に変化なし

---

### スコープ外

- **スキップアイテムの正確なログ記録は行わない**: スキップされたアイテムを`pipeline_stages.jsonl`に記録する機能は本リファクタリングのスコープ外とする。既存のログ記録動作を維持する。

### エッジケース

- 強制終了が各Step実行中に発生した場合、そのアイテムはどう扱われるか？→ 未完了として再処理対象
- `pipeline_stages.jsonl`が破損している場合はどうなるか？→ 警告ログを出力し、破損行をスキップして処理継続
- Extract stageでの1:N展開（チャンク分割）中に中断した場合は？→ 部分展開されたチャンクは無視し、元アイテムから再展開
- Extract stageが未完了の状態でResumeを試みた場合は？→ エラーメッセージを表示して終了（例: `Error: Extract stage not completed. Cannot resume.`）

## 要件 *(必須)*

### 機能要件

- **FR-001**: システムは`BaseStage.run()`メソッド内でResume用のスキップ判定を一元管理しなければならない
- **FR-002**: 継承Stage（Extractor, Transformer, Loader）は`run_with_skip()`メソッドを持たない設計でなければならない
- **FR-003**: スキップ判定は`completed_cache.is_completed(item_id)`を使用して行われなければならない
- **FR-004**: バリデーション失敗等で処理対象外となったアイテムは`ItemStatus.SKIPPED`ではなく、より明確な名前（`INVALID`または`FILTERED`）に設定されなければならない
- **FR-005**: Resume時にスキップされるアイテムはステータス変更せず、処理対象リストから除外されるのみとする
- **FR-006**: ResumeはExtract stageが完了していることが前提条件である。未完了の場合はエラー終了しなければならない
- **FR-007**: Resume開始時に、処理済み件数と処理開始位置を標準出力に表示しなければならない
  - 全体item数: `session.json` の `expected_total_item_count` から取得
  - 処理完了数: `pipeline_stages.jsonl` から `status="success"` をカウント（`session-trace` と同様のロジック）
  - 表示例: `Resume mode: 700/1000 items already completed, starting from item 701`

### キーエンティティ

- **BaseStage**: 全Stageの基底クラス。Resume用スキップロジックを一元管理
- **CompletedItemsCache**: pipeline_stages.jsonlから読み込んだ完了アイテムID群を保持
- **ProcessingItem**: 各アイテムの処理状態を表現。statusを持つ
- **StageContext**: Stage実行コンテキスト。completed_cacheをオプションで保持

### 実装詳細: 現状 vs 変更後

#### 現状の実装（BaseStage.run() 301-315行目）

```python
# Resume mode: Skip already processed items (completed_cache check)
if ctx.completed_cache:
    skipped_items: list[ProcessingItem] = []
    items_to_process: list[ProcessingItem] = []
    for item in items:
        if ctx.completed_cache.is_completed(item.item_id):
            item.status = ItemStatus.SKIPPED           # ステータス変更
            item.metadata["skipped_reason"] = "resume_mode"  # メタデータ追加
            skipped_items.append(item)                 # スキップリストに追加
        else:
            items_to_process.append(item)
    yield from skipped_items  # ← 呼び出し元にスキップアイテムを返す
    items = iter(items_to_process)
```

**問題点**:
- スキップアイテムも yield されるため、呼び出し元でカウントされる
- `ItemStatus.SKIPPED` が設定され、Resume時のスキップとバリデーション失敗が混同

#### 変更後の実装

```python
# Resume mode: Filter out already completed items (no yield, no status change)
if ctx.completed_cache:
    items = (item for item in items
             if not ctx.completed_cache.is_completed(item.item_id))
```

#### 変更点の比較

| 項目 | Before | After |
|------|--------|-------|
| スキップアイテムの yield | あり | なし |
| ステータス変更 | SKIPPED に変更 | 変更なし |
| メタデータ追加 | skipped_reason 追加 | 追加なし |
| 処理 | リスト作成 + yield | ジェネレータでフィルタのみ |

#### 動作の違い

**Before（10件中7件処理済み）**:
```
items: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    ↓
yield: [1(SKIPPED), 2(SKIPPED), ..., 7(SKIPPED), 8, 9, 10]
                    ↓
呼び出し元で受け取る: 10件（うち7件SKIPPED、3件処理）
```

**After（10件中7件処理済み）**:
```
items: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    ↓
filter: [8, 9, 10]  ← 処理済み1-7は除外
                    ↓
呼び出し元で受け取る: 3件のみ
```

#### 呼び出し元への影響（ImportPhase.run()）

```python
# Before: スキップアイテムもカウントされる
for item in loaded:
    if item.status == ItemStatus.COMPLETED:
        items_processed += 1
    elif item.status == ItemStatus.SKIPPED:  # ← Resume時のスキップもここでカウント
        items_skipped += 1

# After: 処理対象のみ受け取る
for item in loaded:
    if item.status == ItemStatus.COMPLETED:
        items_processed += 1
    elif item.status == ItemStatus.FILTERED:  # ← バリデーション失敗のみ
        items_filtered += 1
    # Resume時のスキップはここに来ない（そもそもyieldされない）
```

## 成功基準 *(必須)*

### 測定可能な成果

- **SC-001**: 中断後の再開時、処理済みアイテム（n件）のLLM呼び出しがゼロになる
- **SC-002**: 継承Stageの新規実装で、Resume関連コードの記述が不要になる（認知負荷ゼロ）
- **SC-003**: 既存の`run_with_skip()`メソッド（KnowledgeTransformer, SessionLoader）を削除しても全テストが通過する
