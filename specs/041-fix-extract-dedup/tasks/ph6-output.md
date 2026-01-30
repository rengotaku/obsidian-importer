# Phase 6 Output

## 作業概要
- User Story 4 - INPUT_TYPE と複数 INPUT 対応の実装完了
- FAIL テスト 9 件 (5 ERROR + 4 FAIL) を PASS させた
- CLI 入力インターフェースが統一され、`--input-type` と複数 `--input` をサポート

## 修正ファイル一覧

### プロダクションコード

- `src/etl/cli/commands/import_cmd.py`
  - `--input` を `action="append"` に変更（複数回指定可能、list として保持）
  - `--input-type` 引数を追加（default: `path`, choices: `["path", "url"]`）
  - 入力バリデーションロジックを実装（path 存在チェック、URL 形式チェック）
  - 入力解決ロジックを実装（path: ファイルコピー、url: url.txt 保存）
  - プロバイダー依存の入力処理（`if provider == "github"`）を削除し、`input_type` ベースに統一
  - Resume モードで新旧 URL ファイル（`url.txt` / `github_url.txt`）の両方をサポート

- `src/etl/cli/__init__.py`
  - `run_import()` 関数を更新し、単一 `input_path` を list に変換
  - `input_type="path"` をデフォルトで設定（後方互換性）

- `src/etl/stages/extract/github_extractor.py`
  - `_discover_raw_items()` を更新し、新旧 URL ファイル（`url.txt` / `github_url.txt`）の両方をサポート
  - `url.txt` が複数行対応（最初の行を取得）

### テストコード

- `src/etl/tests/test_cli.py`
  - `test_import_command_with_input()`: `args.input` が list であることを確認
  - `test_import_command_with_options()`: `args.input` が list であることを確認
  - `test_import_command_requires_input()`: argparse が `--input` の有無をチェックしないため、テストロジックを変更

## テスト結果

### Phase 6 新規テスト（RED → GREEN）

```bash
python -m unittest src.etl.tests.test_import_cmd -v
```

結果: **12 tests PASS** ✅

- `test_input_type_defaults_to_path`: PASS
- `test_input_type_path_explicit`: PASS
- `test_input_type_path_copies_files_to_extract_input`: PASS
- `test_input_type_url_accepted`: PASS
- `test_input_type_url_saves_to_url_txt`: PASS
- `test_input_type_url_not_github_url_txt`: PASS
- `test_input_is_repeatable`: PASS
- `test_single_input_is_also_list`: PASS
- `test_multiple_inputs_all_copied`: PASS
- `test_url_without_input_type_fails_path_validation`: PASS
- `test_url_input_type_path_gives_input_not_found`: PASS
- `test_input_type_choices_are_path_and_url`: PASS

### 既存テスト回帰確認

```bash
python -m unittest src.etl.tests.test_cli
```

結果: **36 tests PASS** ✅（全 CLI テストが正常）

## 実装の変更点

### Before（Phase 5 終了時）

```python
# import_cmd.py
parser.add_argument("--input", required=False, help="...")

# execute() 関数
if provider == "github":
    source_path = input_path  # URL 文字列
else:
    input_path = Path(input_path)
    if not input_path.exists():
        return ExitCode.INPUT_NOT_FOUND
    source_path = input_path

# Resume mode
url_file = extract_input_dir / "github_url.txt"

# GitHubExtractor._discover_raw_items()
url_file = input_path / "github_url.txt"
```

### After（Phase 6 完了時）

```python
# import_cmd.py
parser.add_argument("--input", action="append", help="...")
parser.add_argument("--input-type", default="path", choices=["path", "url"], help="...")

# execute() 関数: input_type ベースの処理
for inp in input_list:
    if input_type == "path":
        path = Path(inp)
        if not path.exists():
            return ExitCode.INPUT_NOT_FOUND
    elif input_type == "url":
        if not inp.startswith(("http://", "https://")):
            return ExitCode.ERROR

if input_type == "url":
    url_file = extract_input / "url.txt"
    url_file.write_text("\n".join(input_list), encoding="utf-8")
else:
    for inp in input_list:
        # ファイルまたはディレクトリごとにコピー

# Resume mode: 新旧 URL ファイル両方をサポート
url_file = extract_input_dir / "url.txt"
old_url_file = extract_input_dir / "github_url.txt"
if url_file.exists():
    source_path = url_file.read_text().strip().split("\n")[0]
elif old_url_file.exists():
    source_path = old_url_file.read_text().strip()

# GitHubExtractor._discover_raw_items()
url_file = input_path / "url.txt"
old_url_file = input_path / "github_url.txt"
if url_file.exists():
    github_url = url_file.read_text().strip().split("\n")[0]
elif old_url_file.exists():
    github_url = old_url_file.read_text().strip()
```

## 設計上の改善点

### 1. プロバイダー非依存の入力処理

**Before**:
- GitHub だけ特殊処理（`if provider == "github"`）
- プロバイダーが入力形式を暗黙的に決定
- 将来的に URL 入力が必要な他のプロバイダーを追加困難

**After**:
- `--input-type` で入力形式を明示的に指定
- プロバイダーに依存しない汎用的な入力処理
- 将来的に URL 入力が必要な新プロバイダーを簡単に追加可能

### 2. 複数入力のサポート

**Before**:
- 1 回の実行で 1 ソースのみ処理
- ChatGPT エクスポートが複数 ZIP に分割された場合、複数回実行が必要

**After**:
- `--input` を複数回指定可能（`action="append"`）
- 1 セッションで複数ソースを同時処理
- 効率的なバッチインポート

### 3. URL ファイル名の統一

**Before**:
- GitHub 専用: `github_url.txt`
- プロバイダー依存の命名

**After**:
- 汎用: `url.txt`
- プロバイダー非依存（将来の拡張性向上）
- 後方互換性のため `github_url.txt` も読み込み可能

## 注意点

### 1. 後方互換性

`run_import()` ラッパー関数で、単一 `input_path` を list に変換することで、既存のテストやスクリプトが動作し続ける。

```python
input_list = [input_path] if input_path else None
args.input_type = "path"  # デフォルト
```

### 2. URL ファイル形式の変更

新形式の `url.txt` は複数行対応（将来の複数 URL 入力に備える）:

```text
https://github.com/user/repo1/tree/master/_posts
https://github.com/user/repo2/tree/master/_posts
```

現在は最初の行のみ使用（`split("\n")[0]`）。

### 3. argparse の action="append" の挙動

`action="append"` を使用すると、`required=False` で `--input` を指定しない場合、`args.input` は `None` になる。これは execute() 関数内で validation される。

## 次 Phase への引き継ぎ

### Phase 7 の前提条件

Phase 6 完了により、以下が保証される:

1. **CLI 入力インターフェースの統一**: `--input-type` と複数 `--input` をサポート
2. **プロバイダー非依存**: 入力処理がプロバイダーに依存しない汎用設計
3. **後方互換性**: 既存のテストやスクリプトが動作し続ける

Phase 7（Polish & Cross-Cutting Concerns）では、Makefile の更新、ドキュメント、最終検証を実施する。

## 実装のミス・課題

### なし

Phase 6 は計画通りに完了。テストも全て PASS。

### 将来の改善候補

1. **複数 URL 入力**: 現在は `url.txt` の最初の行のみ使用。将来的に複数 URL を 1 セッションで処理する場合は、Extractor 側の対応が必要
2. **Makefile の INPUT 変数**: カンマ区切りで複数 INPUT を指定できるように Makefile を更新する（Phase 7 で対応）
