# Phase 4 Output

## 作業概要
- Phase 4 - US1 Organize パイプラインの実装完了
- FAIL テスト 29 件を PASS させた
- ジャンル判定、frontmatter 正規化、コンテンツ整形、Vault 配置処理を実装

## 修正ファイル一覧

### 実装ファイル

- `src/obsidian_etl/pipelines/organize/nodes.py` - Organize ノード実装
  - `classify_genre()`: キーワードベースのジャンル判定（tags 優先、次に content）
  - `normalize_frontmatter()`: frontmatter 正規化（不要フィールド削除、normalized=True 設定）
  - `clean_content()`: コンテンツ整形（連続空行削減、行末空白除去）
  - `determine_vault_path()`: ジャンルから Vault パスへのマッピング
  - `move_to_vault()`: Vault ディレクトリへのファイル書き込み

- `src/obsidian_etl/pipelines/organize/pipeline.py` - Organize パイプライン定義
  - 5 つのノードを順序実行: classify_genre → normalize_frontmatter → clean_content → determine_vault_path → move_to_vault
  - 入力: `markdown_notes` (PartitionedDataset)
  - 出力: `organized_items` (PartitionedDataset)

### テスト結果

```
$ python -m unittest tests.pipelines.organize.test_nodes -v
...
Ran 29 tests in 0.003s

OK
```

全テストが PASS。内訳:
- `TestClassifyGenre`: 6 テスト (engineer, business, economy, daily, content からの検出, 複数アイテム)
- `TestClassifyGenreDefault`: 3 テスト (default other, 空タグ, キーワード空)
- `TestNormalizeFrontmatter`: 4 テスト (normalized 設定, 不要フィールド削除, 必須フィールド保持, normalized 追加)
- `TestCleanContent`: 4 テスト (連続空行削減, 単一空行保持, 行末空白除去, frontmatter 保持)
- `TestDetermineVaultPath`: 7 テスト (各ジャンルのマッピング, final_path 構成, 未知ジャンルのフォールバック)
- `TestMoveToVault`: 5 テスト (ファイル書き込み, ディレクトリ自動作成, 複数アイテム, OrganizedItem 返却, UTF-8 エンコーディング)

### リグレッション確認

```
$ python -m unittest tests.pipelines.extract_claude.test_nodes tests.pipelines.transform.test_nodes tests.pipelines.organize.test_nodes -v
...
Ran 67 tests in 0.005s

OK
```

Phase 2 (Extract Claude: 17 テスト) + Phase 3 (Transform: 21 テスト) + Phase 4 (Organize: 29 テスト) = 67 テスト全て PASS。リグレッションなし。

## 実装の詳細

### classify_genre ノード

- **入力**: `dict[str, Callable]` (PartitionedDataset パターン)、params dict
- **処理**:
  1. tags から genre_keywords をマッチング（優先順位: engineer > business > economy > daily）
  2. tags にマッチなし → content から検索
  3. マッチなし → "other"
- **キーワードマッチング戦略**: tags を優先することで、明示的なタグ付けを尊重し、content の偶発的なキーワード出現によるミス分類を防ぐ

### normalize_frontmatter ノード

- **入力**: content に YAML frontmatter を含むアイテム
- **処理**:
  1. YAML frontmatter をパース
  2. 不要フィールド削除: draft, private, slug, lastmod, keywords
  3. normalized: true を設定
  4. 手動フォーマット（2 スペースインデント、list 項目は `  - item` 形式）
- **エラーハンドリング**: YAML パースエラー時は警告ログを出力してスキップ

### clean_content ノード

- **入力**: content を持つアイテム
- **処理**:
  1. frontmatter セクションを検出（`---\n` 開始、`\n---\n` 終了）
  2. body 部分のみをクリーニング（frontmatter は保持）
  3. 連続空行を最大 1 行に削減
  4. 各行の行末空白を除去
- **ヘルパー関数**: `_clean_text()` - 実際のクリーニングロジック

### determine_vault_path ノード

- **入力**: genre フィールドを持つアイテム、params dict
- **処理**:
  1. genre を params["vaults"] マッピングで vault_path に変換
  2. 未知 genre → "other" Vault にフォールバック
  3. final_path = vault_path + output_filename
- **マッピング例**:
  - engineer → Vaults/エンジニア/
  - business → Vaults/ビジネス/
  - economy → Vaults/経済/
  - daily → Vaults/日常/
  - other → Vaults/その他/

### move_to_vault ノード

- **入力**: final_path と content を持つアイテム、params dict
- **処理**:
  1. base_path + final_path で完全パスを構成
  2. 親ディレクトリを自動作成 (mkdir -p 相当)
  3. UTF-8 エンコーディングでファイル書き込み
  4. OrganizedItem dict を返却 (E-4 data model: item_id, file_id, genre, vault_path, final_path, output_filename, metadata)
- **エラーハンドリング**: 書き込み失敗時はエラーログを出力してスキップ

### Organize パイプライン

- **DAG 構造**:
  ```
  markdown_notes
      ↓
  classify_genre (tags/content → genre)
      ↓
  normalize_frontmatter (frontmatter 正規化)
      ↓
  clean_content (body クリーニング)
      ↓
  determine_vault_path (genre → vault_path + final_path)
      ↓
  move_to_vault (ファイル書き込み)
      ↓
  organized_items
  ```

- **中間データセット**:
  - classified_items: genre フィールド追加済み
  - normalized_items: frontmatter 正規化済み
  - cleaned_items: content クリーニング済み
  - vault_determined_items: vault_path, final_path 追加済み
  - organized_items: Vault 配置完了、OrganizedItem 形式

## 次 Phase への引き継ぎ

### Phase 5 (US1 E2E) で必要な情報

- **パイプライン統合**: extract_claude + transform + organize を 1 つの DAG として登録
- **Hook 実装**: ErrorHandlerHook (on_node_error), LoggingHook (before/after_node_run)
- **pipeline_registry**: import_claude パイプラインとして登録
- **E2E テスト**: SequentialRunner で raw_claude → organized_items の一気通貫を検証

### 技術的注意点

- PartitionedDataset パターンは Extract/Transform/Organize で一貫
- params["organize"] に vaults, genre_keywords, base_path を設定
- OrganizedItem (E-4) は item_id, file_id, genre, vault_path, final_path, output_filename, content を含む
- move_to_vault は副作用あり（ファイルシステムへの書き込み）

## 実装のミス・課題

### 初回実装の誤り

**症状**: business/economy/daily のテストが全て engineer に誤分類された

**原因**:
- tags と content を結合して検索していたため、テストヘルパーのデフォルト content（asyncio・フレームワーク関連）が engineer キーワードにマッチ
- 優先順位が engineer 最初のため、他ジャンルのタグがあっても engineer が勝利

**修正**:
1. tags を先にチェック（優先順位: engineer > business > economy > daily）
2. tags にマッチなし → content をチェック
3. これにより明示的なタグ付けを尊重し、content の偶発的キーワード出現を回避

**学び**: テストヘルパーのデフォルト値が実際のテストケースと矛盾する場合、実装の意図を正確に理解する必要がある。test_classify_genre_from_content が「タグにキーワードがなくても、コンテンツからジャンルが検出される」という期待を示していたため、tags 優先 → content フォールバックが正しい戦略と判明。

### 現時点での課題

なし。全テスト PASS。
