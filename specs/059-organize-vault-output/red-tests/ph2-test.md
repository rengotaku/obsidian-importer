# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1 Preview（出力先確認）
- FAIL テスト数: 11 (1 ImportError blocks all test methods)
- テストファイル: `tests/unit/pipelines/vault_output/test_nodes.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_nodes.py | test_resolve_vault_destination_ai_to_engineer | genre=ai -> エンジニア Vault |
| test_nodes.py | test_resolve_vault_destination_with_topic_subfolder | topic がサブフォルダとしてパスに含まれる |
| test_nodes.py | test_resolve_vault_destination_empty_topic | topic 空 -> Vault 直下に配置 |
| test_nodes.py | test_sanitize_topic_special_chars | / と \ がアンダースコアに置換 |
| test_nodes.py | test_sanitize_topic_empty | 空文字列はそのまま返す |
| test_nodes.py | test_sanitize_topic_normal | 通常文字列はそのまま |
| test_nodes.py | test_sanitize_topic_strips_whitespace | 先頭末尾空白除去 |
| test_nodes.py | test_sanitize_topic_unicode | 日本語トピックはそのまま |
| test_nodes.py | test_check_conflicts_detects_existing_file | 既存ファイルで競合検出 |
| test_nodes.py | test_check_conflicts_no_conflict | ファイル未存在で競合なし |
| test_nodes.py | test_log_preview_summary_output_format | サマリー dict に total_files, total_conflicts, vault_distribution |

## テストクラス構成

| クラス | テスト数 | 対象関数 |
|--------|---------|----------|
| TestResolveVaultDestination | 3 | resolve_vault_destination() |
| TestSanitizeTopic | 5 | sanitize_topic() |
| TestCheckConflicts | 2 | check_conflicts() |
| TestLogPreviewSummary | 1 | log_preview_summary() |

## 実装ヒント

- `src/obsidian_etl/pipelines/vault_output/nodes.py` に以下を実装:
  - `sanitize_topic(topic: str) -> str` : / と \ を _ に置換、strip
  - `resolve_vault_destination(organized_files: dict, params: dict) -> dict` : frontmatter から genre/topic/title を抽出し、VaultDestination dict を返す
  - `check_conflicts(destinations: dict) -> list[dict]` : 各 destination の full_path が既に存在するか確認
  - `log_preview_summary(destinations: dict, conflicts: list[dict]) -> dict` : total_files, total_conflicts, vault_distribution を含むサマリー dict を返す
- frontmatter パースには PyYAML を使用（既存パターン参照）
- genre_vault_mapping に存在しない genre は "その他" にフォールバック

## FAIL 出力例
```
ERROR: tests.unit.pipelines.vault_output.test_nodes (unittest.loader._FailedTest.tests.unit.pipelines.vault_output.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.unit.pipelines.vault_output.test_nodes
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/unit/pipelines/vault_output/test_nodes.py", line 20, in <module>
    from obsidian_etl.pipelines.vault_output.nodes import (
        check_conflicts,
        log_preview_summary,
        resolve_vault_destination,
        sanitize_topic,
    )
ModuleNotFoundError: No module named 'obsidian_etl.pipelines.vault_output.nodes'

----------------------------------------------------------------------
Ran 404 tests in 5.538s

FAILED (errors=1)
```
