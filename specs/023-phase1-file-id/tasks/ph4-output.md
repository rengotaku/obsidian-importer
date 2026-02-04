# Phase 4 完了: User Story 2 Continued - Phase 2 での file_id 継承

## 概要

Phase 4 では、Phase 2 実行時に parsed ファイルから file_id を読み取り、出力ファイルに継承する機能を実装した。

## 実行タスク

| タスク | 説明 | 結果 |
|--------|------|------|
| T020 | 前フェーズ出力読み込み | 完了 |
| T021 | `extract_file_id_from_frontmatter()` ヘルパー追加 | 完了 |
| T022 | `cli.py` Phase 2 で file_id 継承処理を実装 | 完了 |
| T023 | Phase 2 file_id 継承テスト追加 (`test_knowledge_extractor.py`) | 完了 |
| T024 | Phase 1 → Phase 2 file_id 一貫性テスト追加 (`test_cli.py`) | 完了 |
| T025 | `make test` で全テストパス確認 | 完了 |
| T026 | Phase 4 出力生成 | 本ファイル |

## 実装内容

### T021: `extract_file_id_from_frontmatter()` ヘルパー関数

**ファイル**: `development/scripts/llm_import/common/knowledge_extractor.py`

```python
def extract_file_id_from_frontmatter(content: str) -> str | None:
    """
    Markdown ファイルの frontmatter から file_id を抽出する (T021)

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

    # file_id を抽出
    file_id_match = re.search(r"^file_id:\s*([a-f0-9]{12})\s*$", frontmatter, re.MULTILINE)
    if file_id_match:
        return file_id_match.group(1)

    return None
```

**機能**:
- 正規表現で frontmatter 内の `file_id:` 行をパース
- 12文字の16進数小文字のみにマッチ（厳密なバリデーション）
- frontmatter 外の `file_id:` にはマッチしない（セキュリティ）

### T022: `cli.py` Phase 2 での file_id 継承

**ファイル**: `development/scripts/llm_import/cli.py`

```python
# T022: file_id を parsed ファイルから継承、なければ新規生成
inherited_file_id: str | None = None
if phase1_path and phase1_path.exists():
    parsed_content = phase1_path.read_text(encoding="utf-8")
    inherited_file_id = extract_file_id_from_frontmatter(parsed_content)

if inherited_file_id:
    # Phase 1 からの継承
    document.file_id = inherited_file_id
else:
    # 新規生成（T011: ファイル書き込み前に生成）
    content_for_hash = document.to_markdown()
    relative_path = output_path.relative_to(output_dir.parent.parent)
    document.file_id = generate_file_id(content_for_hash, relative_path)
```

**変更点**:
- `extract_file_id_from_frontmatter` をインポート
- Phase 2 通常処理で parsed ファイルから file_id を読み取り
- file_id が存在すれば継承、なければ新規生成（後方互換性）

### T023, T024: テストの追加

**ファイル**: `development/scripts/llm_import/tests/test_knowledge_extractor.py`

追加テストクラス `TestExtractFileIdFromFrontmatter`:
- `test_extracts_file_id_from_valid_frontmatter`: 有効な frontmatter から抽出
- `test_extracts_file_id_at_different_position`: 別の位置でも抽出可能
- `test_returns_none_for_missing_file_id`: file_id なしで None
- `test_returns_none_for_no_frontmatter`: frontmatter なしで None
- `test_returns_none_for_invalid_file_id_format`: 無効形式で None
- `test_returns_none_for_empty_content`: 空コンテンツで None
- `test_does_not_match_file_id_outside_frontmatter`: frontmatter 外にはマッチしない

**ファイル**: `development/scripts/llm_import/tests/test_cli.py`

追加テストクラス `TestPhase2FileIdInheritance`:
- `test_phase2_inherits_file_id_from_parsed_file`: Phase 2 が file_id を継承
- `test_phase2_generates_file_id_when_parsed_has_none`: file_id なしで新規生成
- `test_phase1_phase2_file_id_consistency`: Phase 1 → Phase 2 の一貫性

## テスト結果

```
Ran 245 tests in 0.170s
OK (skipped=1)
```

- normalizer テスト: 123件 OK
- 統合テスト: 6件 OK
- llm_import テスト: 116件 OK（+7件追加）

## Phase 2 file_id 継承フロー

```
Phase 1 (parse)
    │
    ├── file_id 生成（コンテンツ + パスからハッシュ）
    ├── parsed ファイルに書き込み
    │   └── frontmatter に file_id: a1b2c3d4e5f6
    │
    ▼
Phase 2 (extract)
    │
    ├── parsed ファイルから file_id 読み取り
    │   └── extract_file_id_from_frontmatter()
    ├── 継承または新規生成
    │   ├── 存在: 継承
    │   └── なし: 新規生成
    ├── KnowledgeDocument.file_id に設定
    └── @index/ に出力
        └── frontmatter に file_id: a1b2c3d4e5f6
```

## 次フェーズへの引き継ぎ

### 利用可能な機能

1. **`extract_file_id_from_frontmatter(content)`** - frontmatter から file_id を抽出
2. **Phase 2 file_id 継承** - parsed ファイルの file_id を Phase 2 出力に継承
3. **後方互換性** - file_id がない parsed ファイルでも新規生成で対応

### Phase 5 での作業

1. `development/scripts/normalizer/` での file_id 維持/生成
2. `@index/` から Vaults へのファイル移動時に file_id を保持
3. file_id がないファイルには新規生成

## Checkpoint 確認

Phase 1 と Phase 2 で file_id が一致:
- Phase 1 で生成した file_id が parsed ファイルに保存される
- Phase 2 で parsed ファイルから file_id を読み取り、継承する
- 両フェーズの出力ファイルで file_id が一致する（テストで検証済み）
- 旧形式（file_id なし）の parsed ファイルにも対応（新規生成）
