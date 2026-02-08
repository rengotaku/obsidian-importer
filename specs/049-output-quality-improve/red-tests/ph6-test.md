# Phase 6 RED Tests

## サマリー
- Phase: Phase 6 - User Story 5: summary/content 逆転の検出
- FAIL テスト数: 1
- テストファイル: tests/pipelines/transform/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_warns_long_summary | summary > 500文字で警告ログ出力 |
| tests/pipelines/transform/test_nodes.py | test_extract_knowledge_no_warning_for_short_summary | summary <= 500文字で警告なし (PASS) |

## テスト詳細

### TestExtractKnowledgeSummaryLength

新規テストクラス（lines 1024-1108）

#### test_extract_knowledge_warns_long_summary (FAIL)

**目的**: FR-009 - システムは 500 文字を超える summary に対して警告ログを出力しなければならない

**テスト内容**:
1. LLM が 501 文字の summary を返す
2. `logger.warning` が "Long summary" を含むメッセージで呼ばれることを検証
3. 警告メッセージに文字数 (501) と partition_id が含まれることを検証
4. アイテムは出力に含まれる（除外されない）ことを検証

**FAIL 理由**: `extract_knowledge` に summary 長さチェック機能が未実装

#### test_extract_knowledge_no_warning_for_short_summary (PASS)

**目的**: 500 文字以下の summary では警告が出ないことを確認

**テスト内容**:
1. LLM が 500 文字（境界値）の summary を返す
2. `logger.warning` が "Long summary" を含まないことを検証
3. アイテムは出力に含まれることを検証

**PASS 理由**: 現状は警告機能自体が未実装なので、警告は出力されない

## 実装ヒント

`src/obsidian_etl/pipelines/transform/nodes.py` の `extract_knowledge` 関数に以下を追加:

```python
# After line 159 (English translation check), before line 161 (Add generated_metadata)
# summary 長さ警告
summary = knowledge.get("summary", "")
if len(summary) > 500:
    logger.warning(f"Long summary ({len(summary)} chars) for {partition_id}")
```

**注意点**:
- 警告のみで、アイテムは除外しない（出力に含める）
- 警告メッセージに文字数と partition_id を含める
- 既存の summary 変数（line 150）が既に存在するので、変数名の競合に注意

## FAIL 出力例

```
======================================================================
FAIL: test_extract_knowledge_warns_long_summary (tests.pipelines.transform.test_nodes.TestExtractKnowledgeSummaryLength.test_extract_knowledge_warns_long_summary)
summary が 500 文字を超える場合、警告ログが出力されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/mock.py", line 1426, in patched
    return func(*newargs, **newkeywargs)
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 1083, in test_extract_knowledge_warns_long_summary
    self.assertIn("Long summary", warning_messages)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Long summary' not found in ''

----------------------------------------------------------------------
Ran 295 tests in 0.812s

FAILED (failures=1)
```

## 関連仕様

- **FR-009**: システムは 500 文字を超える summary に対して警告ログを出力しなければならない
- **SC-005**: summary が 500 文字を超えるケースは 5% 未満になる

## 次ステップ

phase-executor が以下を実行:
1. T050: RED tests 読み込み
2. T051: summary 長さチェック実装
3. T052: 警告ログ出力実装
4. T053: `make test` PASS (GREEN) 確認
