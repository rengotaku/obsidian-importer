# Research: データレイヤー分離

**Feature**: 064-data-layer-separation
**Date**: 2026-03-03

## 1. Kedro データレイヤー規約

### Decision
`05_model_input` を新規レイヤーとして採用。

### Rationale
Kedro の公式ドキュメントでは以下のレイヤー構造を推奨:
- `01_raw`: 生データ（変更不可）
- `02_intermediate`: 中間処理結果
- `03_primary`: 主要な変換結果
- `04_feature`: 機械学習用特徴量
- `05_model_input`: モデル入力用データ
- `06_models`: 学習済みモデル
- `07_model_output`: モデル出力（最終成果物）

JSON 中間データは「モデル（LLM）への入力」であり、`05_model_input` が意味的に適切。

### Alternatives Considered
1. `04_feature` - 却下: ML 特徴量の意味合いが強い
2. `06_models` - 却下: モデル保存用であり、データ保存には不適切
3. `03_primary` に統合 - 却下: 既存データとの混在を避けたい

## 2. iter_with_file_id の役割分析

### Decision
str（Markdown パス）のみサポートに簡素化。

### Rationale
現在の `iter_with_file_id` は 2 種類の入力を処理:
1. **dict**: JSON データから `metadata.file_id` または `file_id` を抽出
2. **str**: Markdown frontmatter から `file_id` を抽出

データレイヤー分離後:
- JSON 処理は `05_model_input` で完結
- `iter_with_file_id` は `07_model_output` の MD ファイルのみを対象
- dict 対応コードは不要になる

### Alternatives Considered
1. 両方サポート継続 - 却下: 複雑性維持の理由がない
2. 別関数に分離 - 却下: dict 用関数の使用箇所がなくなる

## 3. 移行戦略

### Decision
Python スクリプトによる一括移行。

### Rationale
- シンプルな `shutil.move` で十分
- 冪等性: 既存ファイルチェックでスキップ
- dry-run モードで安全確認
- CI/CD への影響なし（ローカル実行のみ）

### Alternatives Considered
1. Makefile ターゲット - 却下: Python の方がエラーハンドリングが容易
2. 手動移動 - 却下: ヒューマンエラーのリスク
3. シェルスクリプト - 却下: クロスプラットフォーム対応が面倒

## 4. 影響範囲分析

### catalog.yml 変更

**移動対象 (JSON → 05_model_input)**:
- `classified_items`
- `existing_classified_items`
- `topic_extracted_items`
- `normalized_items`
- `cleaned_items`
- `vault_determined_items`
- `organized_items`

**維持 (MD → 07_model_output)**:
- `markdown_notes`
- `review_notes`
- `organized_notes`
- `organized_files`

### パイプラインノード影響

catalog.yml のみの変更で、ノードコードの修正は不要。
Kedro の抽象化により、パスはカタログで管理される。

### テスト影響

- fixture のパス参照更新
- 新ディレクトリ構造のテスト追加
- E2E テストは変更なし（Kedro 経由でアクセス）

## 5. 未解決事項

なし。すべての技術的な不明点は解消済み。
