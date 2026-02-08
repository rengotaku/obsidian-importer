# Phase 3 Output

## 作業概要
- User Story 2: タイトルサニタイズ の実装完了
- FAIL テスト 4 件を PASS させた（絵文字除去、ブラケット除去、チルダ/パーセント除去、空タイトルフォールバック）
- `_sanitize_filename` 関数を拡張してファイル名の安全性を向上

## 修正ファイル一覧
- `src/obsidian_etl/pipelines/transform/nodes.py`
  - EMOJI_PATTERN 定数を追加（Unicode 15.1 の絵文字範囲）
  - `_sanitize_filename` 関数を拡張
    - 絵文字除去処理を追加（EMOJI_PATTERN による置換）
    - unsafe_chars を拡張（`[]()~%` を追加）
    - サニタイズ後の空文字列チェックを追加（file_id[:12] へのフォールバック）

## 実装詳細

### 1. EMOJI_PATTERN 定数（line 31-45）

```python
# Emoji ranges from Unicode 15.1
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

主要な Unicode 絵文字範囲をカバー。

### 2. `_sanitize_filename` 関数の拡張

**サニタイズ処理の順序**:
1. 絵文字除去（EMOJI_PATTERN.sub）
2. 危険な文字除去（拡張: `[]()~%` を追加）
3. 空白正規化
4. 長さ制限（250文字）
5. 空文字列フォールバック（file_id[:12]）

**変更前の unsafe_chars**:
```python
unsafe_chars = r'[/\\:*?"<>|]'
```

**変更後の unsafe_chars**:
```python
unsafe_chars = r'[/\\:*?"<>|\[\]()~%]'
```

追加文字:
- `[]` - ブラケット（Obsidian のメタデータ構文と衝突）
- `()` - 括弧（ファイルシステムで問題になる可能性）
- `~` - チルダ（シェルのホームディレクトリ展開と衝突）
- `%` - パーセント（URL エンコーディングと衝突）

## テスト結果

### PASS したテスト
- `test_sanitize_filename_removes_emoji` - 絵文字（🚀📚）が除去される
- `test_sanitize_filename_removes_brackets` - ブラケット `[]()` が除去される
- `test_sanitize_filename_removes_tilde_percent` - チルダ `~` とパーセント `%` が除去される
- `test_sanitize_filename_fallback_to_file_id` - サニタイズ後に空文字列になる場合、file_id[:12] にフォールバック

### 全体テスト結果
```
Ran 293 tests in 0.798s

OK
```

全テスト PASS、リグレッションなし。

## Functional Requirements 達成状況

| FR | 要件 | ステータス |
|----|------|-----------|
| FR-003 | システムはタイトルから絵文字を除去しなければならない | ✅ Complete |
| FR-004 | システムはタイトルからブラケット記号を除去しなければならない | ✅ Complete |
| FR-005 | システムはタイトルからファイルパス記号を除去しなければならない | ✅ Complete |
| FR-006 | システムは空タイトルに file_id ベースの代替を生成しなければならない | ✅ Complete |

## User Story ステータス

### US1: 空コンテンツファイルの除外（Phase 2 完了）
✅ Complete - LLM が空の summary_content を返した場合、アイテムを除外

### US2: タイトルサニタイズ（Phase 3 完了）
✅ Complete - タイトルから絵文字、ブラケット、ファイルパス記号を除去

## 次 Phase への引き継ぎ

### Phase 4: User Story 3 - プレースホルダータイトルの防止
**タスク**:
- プロンプト改善のみ（TDD 対象外）
- `src/obsidian_etl/utils/prompts/knowledge_extraction.txt` を更新
- プレースホルダー禁止ルールを追加（例: `(省略)`, `[トピック名]`, `...`）

**前提**:
- US1, US2 の機能が正常動作している
- テストに影響なし（プロンプト変更のみ）

## 注意点

### ファイル名の安全性向上
タイトルサニタイズにより、以下の問題が解決される:
- **絵文字**: ファイルシステムやバージョン管理システムでの文字化け防止
- **ブラケット**: Obsidian のメタデータ構文との衝突回避
- **チルダ/パーセント**: シェルや URL エンコーディングとの衝突回避

### フォールバック動作
サニタイズ後にタイトルが空になる場合（例: 絵文字のみのタイトル `🚀🚀🚀`）:
- `file_id[:12]` にフォールバック
- 一意性が保証される
- ファイルの追跡可能性を維持

### 既存機能への影響
- ✅ 後方互換性維持（既存のサニタイズロジックを拡張）
- ✅ リグレッションなし（全 293 テスト PASS）
- ✅ US1 の機能に影響なし

## 実装のミス・課題

特になし。全テストが PASS し、要件を完全に満たしている。
