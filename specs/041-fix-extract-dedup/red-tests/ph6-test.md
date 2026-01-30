# Phase 6 RED Tests

## サマリー
- Phase: Phase 6 - User Story 4: INPUT_TYPE と複数 INPUT 対応
- FAIL テスト数: 9 (5 ERROR + 4 FAIL)
- テストファイル: src/etl/tests/test_import_cmd.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 | FAIL 種別 |
|---------------|---------------|---------|-----------|
| test_import_cmd.py | test_input_type_defaults_to_path | `args.input_type` が `"path"` | ERROR: AttributeError (`input_type` 属性なし) |
| test_import_cmd.py | test_input_type_path_explicit | `--input-type path` パース成功 | ERROR: SystemExit (unrecognized arguments) |
| test_import_cmd.py | test_input_type_path_copies_files_to_extract_input | list 入力で execute 正常動作 | ERROR: TypeError (list を Path に変換不可) |
| test_import_cmd.py | test_input_type_url_accepted | `--input-type url` パース成功 | ERROR: SystemExit (unrecognized arguments) |
| test_import_cmd.py | test_input_type_url_saves_to_url_txt | `url.txt` に URL 保存 | FAIL: extract/input ディレクトリ未作成 |
| test_import_cmd.py | test_input_is_repeatable | `--input` 複数回 → list | FAIL: str (最後の値のみ) |
| test_import_cmd.py | test_single_input_is_also_list | `--input` 1 回 → list[1] | FAIL: str (スカラー値) |
| test_import_cmd.py | test_multiple_inputs_all_copied | 複数 ZIP が extract/input/ にコピー | ERROR: TypeError (list を Path に変換不可) |
| test_import_cmd.py | test_url_input_type_path_gives_input_not_found | URL + path → INPUT_NOT_FOUND | FAIL: ERROR(1) != INPUT_NOT_FOUND(2) |

## PASS テスト（既存コードで偶然 PASS するもの）

| テストメソッド | PASS 理由 |
|---------------|----------|
| test_input_type_url_not_github_url_txt | execute() が早期 ERROR return し url.txt 未生成（条件不一致で PASS） |
| test_url_without_input_type_fails_path_validation | 現在の GitHub 分岐で ERROR return（期待通りだが理由が異なる） |
| test_input_type_choices_are_path_and_url | `--input-type invalid` で SystemExit(2)（パーサーにまだ引数がないため） |

## 実装ヒント

- `src/etl/cli/commands/import_cmd.py` の `register()` に以下を追加:
  - `--input-type` 引数: `default="path"`, `choices=["path", "url"]`
  - `--input` を `action="append"` に変更
- `execute()` 関数を修正:
  - `args.input` が list であることを前提に処理
  - `args.input_type == "url"` の場合: URL を `extract/input/url.txt` に保存
  - `args.input_type == "path"` の場合: 従来の Path コピー動作
  - `provider == "github"` の特殊分岐を削除し、`input_type` ベースに統一

## FAIL 出力例

```
ERROR: test_input_type_defaults_to_path (src.etl.tests.test_import_cmd.TestInputTypePathDefault)
AttributeError: 'Namespace' object has no attribute 'input_type'

ERROR: test_input_type_path_explicit (src.etl.tests.test_import_cmd.TestInputTypePathDefault)
SystemExit: 2  # unrecognized arguments: --input-type path

FAIL: test_input_is_repeatable (src.etl.tests.test_import_cmd.TestMultipleInputs)
AssertionError: 'export2.zip' is not an instance of <class 'list'>

FAIL: test_single_input_is_also_list (src.etl.tests.test_import_cmd.TestMultipleInputs)
AssertionError: '/path/to/data' is not an instance of <class 'list'>

ERROR: test_multiple_inputs_all_copied (src.etl.tests.test_import_cmd.TestMultipleInputs)
TypeError: argument should be a str or an os.PathLike object, not 'list'

FAIL: test_url_input_type_path_gives_input_not_found (src.etl.tests.test_import_cmd.TestUrlWithoutInputTypeError)
AssertionError: <ExitCode.ERROR: 1> != <ExitCode.INPUT_NOT_FOUND: 2>
```
