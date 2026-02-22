# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - バリデーションとエラーハンドリング (US4)
- FAIL テスト数: 9 (7 FAIL + 2 ERROR)
- PASS テスト数: 2 (既存動作と一致するテスト)
- テストファイル: tests/pipelines/organize/test_nodes.py
- テストクラス: TestGenreConfigValidation

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|---------------|---------------|---------|---------|
| test_nodes.py | test_missing_description_warning_logs | description 欠落時に logger.warning が呼ばれる | warning が呼ばれない |
| test_nodes.py | test_missing_vault_raises_error | vault 欠落時に ValueError/KeyError が発生 | 例外が発生しない |
| test_nodes.py | test_missing_vault_error_message_clarity | vault 欠落エラーメッセージにジャンル名と "vault" を含む | 例外が発生しない |
| test_nodes.py | test_missing_vault_with_valid_genres_mixed | 正常+vault欠落混在時にエラー発生 | 例外が発生しない |
| test_nodes.py | test_empty_genre_mapping_returns_fallback | 空の mapping で other フォールバック + warning | warning が呼ばれない |
| test_nodes.py | test_empty_genre_mapping_fallback_genre_definitions | 空の mapping で genre_definitions に other 含む | other が genre_definitions にない |
| test_nodes.py | test_empty_genre_mapping_warning_content | 空の mapping で適切な警告メッセージ | warning が呼ばれない |
| test_nodes.py | test_none_genre_mapping_returns_fallback | None mapping で other フォールバック + warning | AttributeError (None.items()) |
| test_nodes.py | test_none_genre_mapping_fallback_genre_definitions | None mapping で genre_definitions に other 含む | AttributeError (None.items()) |

## PASS テスト (既存動作で PASS)

| テストメソッド | 理由 |
|---------------|------|
| test_missing_description_does_not_raise | 現行実装は description 欠落でも例外を出さない |
| test_missing_description_uses_genre_name_as_fallback | 現行実装は genre_key をフォールバックに使用 |

## 実装ヒント

- `src/obsidian_etl/pipelines/organize/nodes.py` の `_parse_genre_config()` に以下を追加:
  1. `genre_vault_mapping` が None/空の場合: 警告ログ + `{"other": "other"}` と `{"other"}` を返す
  2. 各ジャンルの `vault` キー存在チェック: なければ `ValueError` を送出
  3. `description` キー欠落時: `logger.warning()` で警告出力（動作は継続）

## FAIL 出力例
```
FAIL: test_missing_description_warning_logs (tests.pipelines.organize.test_nodes.TestGenreConfigValidation)
AssertionError: Expected 'warning' to have been called.

FAIL: test_missing_vault_raises_error (tests.pipelines.organize.test_nodes.TestGenreConfigValidation)
AssertionError: (<class 'ValueError'>, <class 'KeyError'>) not raised

FAIL: test_empty_genre_mapping_returns_fallback (tests.pipelines.organize.test_nodes.TestGenreConfigValidation)
AssertionError: Expected 'warning' to have been called.

ERROR: test_none_genre_mapping_returns_fallback (tests.pipelines.organize.test_nodes.TestGenreConfigValidation)
AttributeError: 'NoneType' object has no attribute 'items'
```
