# Research: Resume機能の基底クラス集約リファクタリング

**Branch**: `039-resume-baseclass-refactor` | **Date**: 2026-01-27

## 1. ItemStatus.SKIPPED の名前変更

### 決定

`ItemStatus.SKIPPED` → `ItemStatus.FILTERED` に変更

### 根拠

- `FILTERED` は「条件でふるい落とされた」というニュアンスを明確に表現
- Resume時の「スキップ」（処理済みアイテムを除外）との混同を避ける
- `validate_input()` の結果と直接対応する意味を持つ
- 代替案 `INVALID` は「データが不正」という意味合いが強すぎる

### 影響範囲

| ファイル | 変更内容 |
|----------|----------|
| `src/etl/core/status.py` | Enum定義変更 |
| 他15ファイル | `ItemStatus.SKIPPED` → `ItemStatus.FILTERED` |

### 代替案の検討

| 候補 | 評価 | 却下理由 |
|------|------|----------|
| `INVALID` | △ | バリデーション失敗以外のケースにも使用される |
| `EXCLUDED` | △ | 曖昧、何から除外されたか不明確 |
| `INELIGIBLE` | △ | 長すぎる、技術用語として馴染みが薄い |

---

## 2. Resume時のスキップ実装方式

### 決定

- Resume時は `ItemStatus` を変更せず、処理対象リストから除外するのみ
- `yield` せずに次のアイテムへ進む（現状は `yield` している）

### 根拠

- 前回の処理結果（COMPLETED, FAILED等）を保持すべき
- ステータス変更が不要なら、処理を単純化できる
- ログ記録もスコープ外のため、yield不要

### 現状実装 (BaseStage.run() 301-315行目)

```python
if ctx.completed_cache.is_completed(item.item_id):
    item.status = ItemStatus.SKIPPED  # ← 削除
    item.metadata["skipped_reason"] = "resume_mode"  # ← 削除
    skipped_items.append(item)  # ← 削除
# ...
yield from skipped_items  # ← 削除
```

### 新実装

```python
if ctx.completed_cache:
    items = (item for item in items if not ctx.completed_cache.is_completed(item.item_id))
```

---

## 3. run_with_skip() メソッドの削除

### 決定

`KnowledgeTransformer.run_with_skip()` と `SessionLoader.run_with_skip()` を削除

### 根拠

- `BaseStage.run()` に Resume ロジックが集約されているため不要
- 継承クラスが Resume を意識しない設計に移行

### 影響範囲

| ファイル | 変更内容 |
|----------|----------|
| `src/etl/stages/transform/knowledge_transformer.py` | `run_with_skip()` 削除 (656-702行) |
| `src/etl/stages/load/session_loader.py` | `run_with_skip()` 削除 (341-388行) |
| テストファイル | 関連テストの修正または削除 |

---

## 4. Resume前提条件のチェック

### 決定

Resume時に Extract stage 完了を確認し、未完了ならエラー終了

### 実装方法

`ImportPhase.run()` または CLI レベルで以下をチェック：
1. `session.json` が存在する
2. `expected_total_item_count` が設定されている
3. `extract/output/` にファイルが存在する

### エラーメッセージ

```
Error: Extract stage not completed. Cannot resume.
Run without --session to start fresh, or complete Extract stage first.
```

---

## 5. Resume進捗表示の実装

### 決定

Resume開始時に処理済み件数と処理開始位置を表示

### データ取得方法

| データ | 取得元 |
|--------|--------|
| 全体item数 | `session.json` → `expected_total_item_count` |
| 処理完了数 | `pipeline_stages.jsonl` → `status="success"` カウント |

### 表示フォーマット

```
Resume mode: 700/1000 items already completed, starting from item 701
```

### 実装場所

`ImportPhase.run()` の Resume モード開始時

---

## 6. 既存テストへの影響

### 影響を受けるテストファイル

| ファイル | 影響 |
|----------|------|
| `test_resume_mode.py` | `ItemStatus.SKIPPED` → `FILTERED` 変更、run_with_skip テスト削除 |
| `test_knowledge_transformer.py` | `SKIPPED` 参照の変更 |
| `test_stages.py` | `SKIPPED` 参照の変更 |
| `test_import_phase.py` | `SKIPPED` カウントの変更 |

### テスト方針

- 既存テストの `SKIPPED` を `FILTERED` に置換
- `run_with_skip()` 関連テストは削除
- Resume機能のテストは `BaseStage.run()` 経由に統一
