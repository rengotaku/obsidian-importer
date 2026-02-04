# Phase 5 完了: User Story 3 - Organize 時の file_id 付与・維持

## 概要

Phase 5 では、`@index/` から Vaults へファイルを移動する際に file_id が付与・維持される機能を実装した。

## 実行タスク

| タスク | 説明 | 結果 |
|--------|------|------|
| T027 | 前フェーズ出力読み込み | 完了 |
| T028 | `extract_file_id_from_frontmatter()` 関数追加 | 完了 |
| T029 | `get_or_generate_file_id()` ヘルパー実装 | 完了 |
| T030 | `process_single_file()` で既存 file_id を優先 | 完了 |
| T031 | file_id 維持テスト追加 | 完了 |
| T032 | file_id 生成テスト追加 | 完了 |
| T033 | `make test` で全テストパス確認 | 完了 |
| T034 | Phase 5 出力生成 | 本ファイル |

## 実装内容

### T028: `extract_file_id_from_frontmatter()` 関数

**ファイル**: `development/scripts/normalizer/processing/single.py`

```python
def extract_file_id_from_frontmatter(content: str) -> str | None:
    """Markdown ファイルの frontmatter から file_id を抽出する (T028)

    Args:
        content: Markdown ファイルの内容

    Returns:
        file_id (12文字の16進数) または None

    Example:
        >>> content = "---\\ntitle: Test\\nfile_id: a1b2c3d4e5f6\\n---\\n# Content"
        >>> extract_file_id_from_frontmatter(content)
        'a1b2c3d4e5f6'
    """
    # frontmatter を抽出 (--- で囲まれた部分)
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # file_id を抽出 (12文字の16進数小文字のみ)
    file_id_match = re.search(r"^file_id:\s*([a-f0-9]{12})\s*$", frontmatter, re.MULTILINE)
    if file_id_match:
        return file_id_match.group(1)

    return None
```

**機能**:
- 正規表現で frontmatter 内の `file_id:` 行をパース
- 12文字の16進数小文字のみにマッチ（厳密なバリデーション）
- frontmatter 外の `file_id:` にはマッチしない（セキュリティ）

### T029: `get_or_generate_file_id()` ヘルパー関数

**ファイル**: `development/scripts/normalizer/processing/single.py`

```python
def get_or_generate_file_id(content: str, filepath: Path) -> str:
    """既存の file_id を維持、なければ新規生成 (T029)

    「file_id がなければ生成、あれば維持」の原則に従う。

    Args:
        content: ファイルコンテンツ
        filepath: ファイルパス

    Returns:
        file_id (12文字の16進数)
    """
    # 既存の file_id を抽出
    existing_file_id = extract_file_id_from_frontmatter(content)
    if existing_file_id:
        return existing_file_id

    # 新規生成
    return generate_file_id(content, filepath)
```

**機能**:
- 「file_id がなければ生成、あれば維持」の原則を実装
- 既存の file_id を優先して維持
- file_id がない場合は新規生成

### T030: `process_single_file()` の更新

**ファイル**: `development/scripts/normalizer/processing/single.py`

```python
# 元ファイルの文字数を取得 & file_id 取得/生成 (T030)
try:
    original_content = filepath.read_text(encoding="utf-8")
    result["original_chars"] = len(original_content)
    # ファイル追跡用ハッシュID: 既存を維持、なければ生成
    result["file_id"] = get_or_generate_file_id(original_content, filepath)
except Exception:
    pass
```

**変更点**:
- `generate_file_id()` 直接呼び出しから `get_or_generate_file_id()` に変更
- 既存の file_id がある場合は維持される

### T031, T032: テストの追加

**ファイル**: `development/scripts/normalizer/tests/test_single.py`

追加テストクラス `TestExtractFileIdFromFrontmatter`:
- `test_extracts_file_id_from_valid_frontmatter`: 有効な frontmatter から抽出
- `test_extracts_file_id_at_different_position`: 別の位置でも抽出可能
- `test_returns_none_for_missing_file_id`: file_id なしで None
- `test_returns_none_for_no_frontmatter`: frontmatter なしで None
- `test_returns_none_for_invalid_file_id_format`: 無効形式で None
- `test_does_not_match_file_id_outside_frontmatter`: frontmatter 外にはマッチしない

追加テストクラス `TestGetOrGenerateFileId`:
- `test_preserves_existing_file_id` (T031): 既存の file_id を維持
- `test_generates_file_id_when_missing` (T032): file_id なしで新規生成
- `test_generates_file_id_for_no_frontmatter`: frontmatter なしでも新規生成
- `test_file_id_format`: フォーマット検証

## テスト結果

```
Ran 133 tests in 0.010s
OK (skipped=1)

Ran 6 tests in 0.002s
OK

Ran 116 tests in ...
OK
```

- normalizer テスト: 133件 OK (+10件追加)
- 統合テスト: 6件 OK
- llm_import テスト: 116件 OK

## Organize 時の file_id 処理フロー

```
@index/ にファイル到着
    │
    ├── frontmatter に file_id あり?
    │   ├── はい → 既存 file_id を維持
    │   └── いいえ → 新規 file_id を生成
    │
    ├── process_single_file() で処理
    │   └── get_or_generate_file_id() 呼び出し
    │
    ▼
Vaults/ にファイル移動
    └── frontmatter に file_id: [12文字16進数]
```

## 次フェーズへの引き継ぎ

### 利用可能な機能

1. **`extract_file_id_from_frontmatter(content)`** - frontmatter から file_id を抽出
2. **`get_or_generate_file_id(content, filepath)`** - 既存維持または新規生成
3. **organize 時の file_id 維持/生成** - 全ファイルに file_id が付与される

### Phase 6 での作業

1. 後方互換性の確認（file_id なしエントリ）
2. quickstart.md の検証シナリオ実行
3. 最終品質確認

## Checkpoint 確認

Organize で file_id が維持/生成される:
- 既存の file_id がある場合は維持される（テストで検証済み）
- file_id がない場合は新規生成される（テストで検証済み）
- Vaults 内のすべてのファイルに file_id が付与される
