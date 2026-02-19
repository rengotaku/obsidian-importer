# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - User Story 1 振り分けプレビュー確認
- FAIL テスト数: 12 メソッド (5 クラス)
- テストファイル: tests/test_organize_files.py
- FAIL 原因: ImportError (関数が未実装)

## FAIL テスト一覧

| テストファイル | テストクラス | テストメソッド | 期待動作 |
|---------------|-------------|---------------|---------|
| tests/test_organize_files.py | TestLoadConfig | test_load_config_success | YAML設定ファイルを読み込みdict返却 |
| tests/test_organize_files.py | TestLoadConfig | test_load_config_not_found | 存在しないパスでFileNotFoundError |
| tests/test_organize_files.py | TestParseFrontmatter | test_parse_frontmatter | frontmatter付き.mdからdict抽出 |
| tests/test_organize_files.py | TestParseFrontmatter | test_parse_frontmatter_invalid | frontmatterなし.mdで空dict/None |
| tests/test_organize_files.py | TestGetGenreMapping | test_get_genre_mapping | engineer->エンジニア等のマッピング |
| tests/test_organize_files.py | TestGetGenreMapping | test_get_genre_mapping_unknown | 未知ジャンル->その他フォールバック |
| tests/test_organize_files.py | TestSanitizeTopic | test_sanitize_topic | /: *等の特殊文字を_に置換 |
| tests/test_organize_files.py | TestSanitizeTopic | test_sanitize_topic_with_various_special_chars | \?<>"| 等の置換 |
| tests/test_organize_files.py | TestSanitizeTopic | test_sanitize_topic_unicode | 日本語文字列の保持 |
| tests/test_organize_files.py | TestSanitizeTopic | test_sanitize_topic_empty | 空文字列の処理 |
| tests/test_organize_files.py | TestPreview | test_preview_genre_counts | ジャンル別件数の集計表示 |
| tests/test_organize_files.py | TestPreview | test_preview_folder_existence | 出力フォルダ存在確認 |
| tests/test_organize_files.py | TestPreview | test_preview_empty_input | ファイル0件時のメッセージ |

## 実装ヒント

### 必要な関数 (scripts/organize_files.py)

| 関数 | シグネチャ | 説明 |
|------|-----------|------|
| `load_config` | `load_config(path: str) -> dict` | YAML設定ファイル読み込み。PyYAML使用 |
| `parse_frontmatter` | `parse_frontmatter(path: str) -> dict | None` | .mdファイルからYAML frontmatter抽出 |
| `get_genre_mapping` | `get_genre_mapping(config: dict, genre: str) -> str` | 英語ジャンル->日本語変換。未知は'その他' |
| `sanitize_topic` | `sanitize_topic(topic: str) -> str` | OS安全でない文字を_に置換 |
| `scan_files` | `scan_files(input_dir: str) -> list` | .mdファイル一覧取得 |
| `generate_preview` | `generate_preview(config: dict, input_dir: str, output_dir: str = None) -> str` | プレビュー文字列生成 |

### 技術的な注意点

- `load_config`: PyYAML (`yaml.safe_load`) を使用
- `parse_frontmatter`: `---` で囲まれたYAMLブロックを抽出し `yaml.safe_load` でパース
- `sanitize_topic`: `/ \ : * ? " < > |` を `_` に置換。日本語・Unicode文字は保持
- `generate_preview`: `scan_files` + `parse_frontmatter` + `get_genre_mapping` を組み合わせ

## FAIL 出力例

```
======================================================================
ERROR: tests.test_organize_files (unittest.loader._FailedTest.tests.test_organize_files)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.test_organize_files
Traceback (most recent call last):
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
  File "/home/takuya/.anyenv/envs/pyenv/versions/3.13.11/lib/python3.13/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/data/projects/obsidian-importer/tests/test_organize_files.py", line 9, in <module>
    from scripts.organize_files import (
    ...
    )
ImportError: cannot import name 'generate_preview' from 'scripts.organize_files'
----------------------------------------------------------------------
Ran 356 tests in 7.833s
FAILED (errors=1)
```
