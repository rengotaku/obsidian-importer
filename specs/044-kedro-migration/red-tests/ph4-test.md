# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - US1 Organize パイプライン
- FAIL テスト数: 26 (6 test classes)
- テストファイル: tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_engineer | エンジニア関連タグが 'engineer' に分類 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_business | ビジネス関連タグが 'business' に分類 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_economy | 経済関連タグが 'economy' に分類 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_daily | 日常関連タグが 'daily' に分類 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_from_content | コンテンツ内キーワードからジャンル検出 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenre.test_classify_genre_multiple_items | 複数アイテムの個別ジャンル分類 |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenreDefault.test_classify_genre_default_other | キーワード不一致時 'other' にフォールバック |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenreDefault.test_classify_genre_empty_tags | 空タグ+キーワード不一致 → 'other' |
| tests/pipelines/organize/test_nodes.py | TestClassifyGenreDefault.test_classify_genre_no_genre_keywords_param | genre_keywords 空 → 全て 'other' |
| tests/pipelines/organize/test_nodes.py | TestNormalizeFrontmatter.test_normalize_frontmatter_sets_normalized_true | normalized=True が設定される |
| tests/pipelines/organize/test_nodes.py | TestNormalizeFrontmatter.test_normalize_frontmatter_removes_unnecessary_fields | draft, slug, lastmod 等の不要フィールド削除 |
| tests/pipelines/organize/test_nodes.py | TestNormalizeFrontmatter.test_normalize_frontmatter_preserves_essential_fields | title, created, tags, file_id が保持 |
| tests/pipelines/organize/test_nodes.py | TestNormalizeFrontmatter.test_normalize_frontmatter_adds_normalized_when_missing | normalized 未設定時に追加 |
| tests/pipelines/organize/test_nodes.py | TestCleanContent.test_clean_content_removes_excess_blank_lines | 3行以上の空行を最大1行に削減 |
| tests/pipelines/organize/test_nodes.py | TestCleanContent.test_clean_content_preserves_single_blank_line | 段落間の1行空行を保持 |
| tests/pipelines/organize/test_nodes.py | TestCleanContent.test_clean_content_strips_trailing_whitespace | 行末空白の除去 |
| tests/pipelines/organize/test_nodes.py | TestCleanContent.test_clean_content_preserves_frontmatter | frontmatter を変更しない |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_engineer | engineer → Vaults/エンジニア/ |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_business | business → Vaults/ビジネス/ |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_economy | economy → Vaults/経済/ |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_daily | daily → Vaults/日常/ |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_other | other → Vaults/その他/ |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_includes_final_path | final_path = vault_path + output_filename |
| tests/pipelines/organize/test_nodes.py | TestDetermineVaultPath.test_determine_vault_path_unknown_genre_fallback | 未知ジャンル → other Vault にフォールバック |
| tests/pipelines/organize/test_nodes.py | TestMoveToVault.test_move_to_vault_writes_file | ファイルが正しいパスに書き込まれる |
| tests/pipelines/organize/test_nodes.py | TestMoveToVault.test_move_to_vault_creates_directories | Vault ディレクトリを自動作成 |
| tests/pipelines/organize/test_nodes.py | TestMoveToVault.test_move_to_vault_multiple_items | 複数アイテムを各 Vault に配置 |
| tests/pipelines/organize/test_nodes.py | TestMoveToVault.test_move_to_vault_returns_organized_items | OrganizedItem (E-4) 形式の dict を返す |
| tests/pipelines/organize/test_nodes.py | TestMoveToVault.test_move_to_vault_utf8_encoding | 日本語を UTF-8 で正しく書き込み |

## 実装ヒント

- `src/obsidian_etl/pipelines/organize/nodes.py` に以下の関数を実装:
  - `classify_genre(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]`
    - tags + content のキーワードマッチングで genre を判定
    - params["genre_keywords"] から各ジャンルのキーワードリストを取得
    - マッチなし → "other"
  - `normalize_frontmatter(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]`
    - YAML frontmatter をパースし、不要フィールド (draft, private, slug, lastmod, keywords) を除去
    - normalized: true を追加/更新
  - `clean_content(partitioned_input: dict[str, Callable]) -> dict[str, dict]`
    - 連続空行を最大1行に削減
    - 行末空白を除去
    - frontmatter は変更しない
  - `determine_vault_path(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]`
    - params["vaults"] から genre → vault_path マッピング
    - final_path = vault_path + output_filename
    - 未知 genre は "other" にフォールバック
  - `move_to_vault(partitioned_input: dict[str, Callable], params: dict) -> dict[str, dict]`
    - params["base_path"] + final_path にファイル書き込み
    - ディレクトリを自動作成 (mkdir -p)
    - UTF-8 エンコーディング
    - OrganizedItem (E-4) 形式の dict を返す

## FAIL 出力例
```
ERROR: pipelines.organize.test_nodes (unittest.loader._FailedTest.pipelines.organize.test_nodes)
ImportError: Failed to import test module: test_nodes
ImportError: cannot import name 'classify_genre' from 'obsidian_etl.pipelines.organize.nodes'
```
