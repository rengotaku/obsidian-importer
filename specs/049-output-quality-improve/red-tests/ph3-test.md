# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - User Story 2: タイトルサニタイズ
- FAIL テスト数: 4
- テストファイル: `tests/pipelines/transform/test_nodes.py`

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/transform/test_nodes.py | test_sanitize_filename_removes_emoji | 絵文字が除去される |
| tests/pipelines/transform/test_nodes.py | test_sanitize_filename_removes_brackets | ブラケット `[]()` が除去される |
| tests/pipelines/transform/test_nodes.py | test_sanitize_filename_removes_tilde_percent | チルダ `~` とパーセント `%` が除去される |
| tests/pipelines/transform/test_nodes.py | test_sanitize_filename_fallback_to_file_id | 空タイトル時に file_id[:12] にフォールバック |

## 実装ヒント

### 1. EMOJI_PATTERN 定数追加

`src/obsidian_etl/pipelines/transform/nodes.py` のモジュールレベルに追加:

```python
import re

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U00002702-\U000027B0"  # Dingbats
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002600-\U000026FF"  # Misc symbols
    "]+",
    flags=re.UNICODE
)
```

### 2. `_sanitize_filename` 関数拡張

既存の `_sanitize_filename` を以下のように拡張:

```python
def _sanitize_filename(title: str, file_id: str) -> str:
    if not title or not title.strip():
        return file_id[:12]

    # 1. 絵文字除去
    sanitized = EMOJI_PATTERN.sub("", title)

    # 2. 問題文字除去（拡張: []()~% を追加）
    unsafe_chars = r'[/\\:*?"<>|\[\]()~%]'
    sanitized = re.sub(unsafe_chars, "", sanitized)

    # 3. 空白正規化
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # 4. フォールバック
    if not sanitized:
        return file_id[:12]

    return sanitized[:250]
```

### 変更点

| 項目 | 現在 | 変更後 |
|------|------|--------|
| 絵文字除去 | なし | EMOJI_PATTERN で除去 |
| ブラケット | 除去しない | `[]()` を除去 |
| パス記号 | `/\:*?"<>\|` のみ | `~%` を追加 |
| 空タイトルフォールバック | 入力時のみチェック | サニタイズ後もチェック |

## FAIL 出力例

```
======================================================================
FAIL: test_sanitize_filename_removes_emoji (tests.pipelines.transform.test_nodes.TestSanitizeFilename.test_sanitize_filename_removes_emoji)
タイトルから絵文字が除去されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 943, in test_sanitize_filename_removes_emoji
    self.assertNotIn("🚀", result)
AssertionError: '🚀' unexpectedly found in '🚀 Python入門 📚'

======================================================================
FAIL: test_sanitize_filename_removes_brackets (tests.pipelines.transform.test_nodes.TestSanitizeFilename.test_sanitize_filename_removes_brackets)
タイトルからブラケット記号が除去されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 967, in test_sanitize_filename_removes_brackets
    self.assertNotIn("[", result)
AssertionError: '[' unexpectedly found in 'React [入門] (2026)'

======================================================================
FAIL: test_sanitize_filename_removes_tilde_percent (tests.pipelines.transform.test_nodes.TestSanitizeFilename.test_sanitize_filename_removes_tilde_percent)
タイトルからチルダとパーセント記号が除去されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 992, in test_sanitize_filename_removes_tilde_percent
    self.assertNotIn("~", result)
AssertionError: '~' unexpectedly found in '~home100% Complete'

======================================================================
FAIL: test_sanitize_filename_fallback_to_file_id (tests.pipelines.transform.test_nodes.TestSanitizeFilename.test_sanitize_filename_fallback_to_file_id)
サニタイズ後にタイトルが空になる場合、file_id[:12] がフォールバックとして使用されること。
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/data/projects/obsidian-importer/tests/pipelines/transform/test_nodes.py", line 1017, in test_sanitize_filename_fallback_to_file_id
    self.assertEqual(result, file_id[:12])
AssertionError: '🚀🚀🚀' != 'abc123def456'

----------------------------------------------------------------------
Ran 293 tests in 0.798s

FAILED (failures=4)
```

## テストクラス構造

```python
class TestSanitizeFilename(unittest.TestCase):
    """_sanitize_filename: title sanitization for filenames.

    Tests for User Story 2 - タイトルサニタイズ
    タイトルから絵文字、ブラケット、ファイルパス記号を除去する。
    """

    def test_sanitize_filename_removes_emoji(self):
        """FR-003: 絵文字除去"""

    def test_sanitize_filename_removes_brackets(self):
        """FR-004: ブラケット除去"""

    def test_sanitize_filename_removes_tilde_percent(self):
        """FR-005: パス記号除去"""

    def test_sanitize_filename_fallback_to_file_id(self):
        """FR-006: 空タイトルフォールバック"""
```

## Functional Requirements マッピング

| テスト | FR | 説明 |
|--------|-----|------|
| test_sanitize_filename_removes_emoji | FR-003 | システムはタイトルから絵文字を除去しなければならない |
| test_sanitize_filename_removes_brackets | FR-004 | システムはタイトルからブラケット記号を除去しなければならない |
| test_sanitize_filename_removes_tilde_percent | FR-005 | システムはタイトルからファイルパス記号を除去しなければならない |
| test_sanitize_filename_fallback_to_file_id | FR-006 | システムは空タイトルに file_id ベースの代替を生成しなければならない |
