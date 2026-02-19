# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 2 ファイル振り分け実行
- FAIL テスト数: 14
- テストファイル: tests/test_organize_files.py

## FAIL テスト一覧

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestGetDestinationPath | test_get_destination_path | genre=engineer, topic=Python -> OUTPUT/エンジニア/Python/file.md |
| TestGetDestinationPath | test_get_destination_path_economy | genre=economy -> OUTPUT/経済/スマートフォン/file.md |
| TestGetDestinationPath | test_get_destination_path_special_topic | topic の特殊文字がサニタイズされる |
| TestGetDestinationPath | test_get_destination_unclassified_no_genre | genre なし -> OUTPUT/unclassified/file.md |
| TestGetDestinationPath | test_get_destination_unclassified_empty_genre | genre 空文字 -> OUTPUT/unclassified/file.md |
| TestGetDestinationPath | test_get_destination_no_topic | topic なし -> OUTPUT/日常/file.md (genre直下) |
| TestMoveFile | test_move_file_success | source が消え dest に同内容が存在、"success" 返却 |
| TestMoveFile | test_move_file_creates_directory | 存在しないディレクトリを自動作成してファイル移動 |
| TestMoveFile | test_move_file_skip_existing | dest に同名ファイルがある場合スキップ、"skipped" 返却 |
| TestMoveFile | test_move_file_source_not_found | 存在しない source で "error" 返却 |
| TestOrganizeFiles | test_organize_files_summary | total=4, success=4, skipped=0, error=0 |
| TestOrganizeFiles | test_organize_files_with_existing_dest | total=1, skipped=1, success=0 |
| TestOrganizeFiles | test_organize_files_empty_input | 全カウント 0 のサマリー |
| TestOrganizeFiles | test_organize_files_genre_counts | by_genre にジャンル別件数が正しく記録 |

## 実装ヒント

### get_destination_path(config, frontmatter, filename, output_dir) -> Path
- `config["genre_mapping"]` で英語genre -> 日本語フォルダ名変換
- `config["unclassified_folder"]` で genre なし/空のフォールバック先
- genre が空文字 or 未設定 -> unclassified フォルダ直下
- topic あり -> `output_dir / genre_ja / sanitized_topic / filename`
- topic なし -> `output_dir / genre_ja / filename`
- `sanitize_topic()` で topic の特殊文字をサニタイズ

### move_file(source, dest) -> str
- source が存在しない -> "error" 返却
- dest が既に存在 -> "skipped" 返却 (source はそのまま)
- dest 親ディレクトリが存在しない -> `mkdir(parents=True)` で自動作成
- 正常移動 -> `shutil.move()` で移動、"success" 返却

### organize_files(config, input_dir, output_dir) -> dict
- `scan_files()` でファイル一覧取得
- 各ファイルに `get_destination_path()` でパス計算
- `move_file()` で移動
- 戻り値: `{"total": int, "success": int, "skipped": int, "error": int, "by_genre": dict}`

## FAIL 出力例
```
ERROR: test_get_destination_path (tests.test_organize_files.TestGetDestinationPath.test_get_destination_path)
genre と topic から正しいターゲットパスが計算されること.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/test_organize_files.py", line 265, in setUp
    from scripts.organize_files import get_destination_path
ImportError: cannot import name 'get_destination_path' from 'scripts.organize_files'

ERROR: test_move_file_success (tests.test_organize_files.TestMoveFile.test_move_file_success)
ファイルが正常に移動されること.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/test_organize_files.py", line 352, in setUp
    from scripts.organize_files import move_file
ImportError: cannot import name 'move_file' from 'scripts.organize_files'

ERROR: test_organize_files_summary (tests.test_organize_files.TestOrganizeFiles.test_organize_files_summary)
処理サマリーに success/skip/error の件数が正しく含まれること.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/test_organize_files.py", line 428, in setUp
    from scripts.organize_files import organize_files
ImportError: cannot import name 'organize_files' from 'scripts.organize_files'

----------------------------------------------------------------------
Ran 382 tests in 5.573s
FAILED (errors=14)
```
