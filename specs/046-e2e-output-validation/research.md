# Research: E2Eテスト出力検証

## R-1: テキスト類似度の計算方法

### Decision
Python標準ライブラリの `difflib.SequenceMatcher` を使用する。

### Rationale
- 外部依存を追加せずに済む（プロジェクト方針: 標準ライブラリ中心）
- `SequenceMatcher.ratio()` は0.0〜1.0の類似度を返し、90%閾値の判定に直接使える
- Markdown テキストの比較に十分な精度がある
- フロンティマター部分とボディ部分を分離して比較すれば、構造的類似度と内容類似度を別々に計算可能

### Alternatives considered
- **Levenshtein距離 (python-Levenshtein)**: 外部依存が必要。文字レベルの比較でMarkdownには過剰
- **cosine similarity (scikit-learn)**: 外部依存が大きすぎる。セマンティックな類似度は不要
- **diff コマンド (subprocess)**: プラットフォーム依存。Python内で完結しない

## R-2: ゴールデンファイルの比較戦略

### Decision
Markdown を frontmatter と body に分離し、それぞれ異なる方法で比較する。

- **frontmatter**: YAML をパースし、キーの存在と値の類似度をチェック。`created` や `file_id` など固定値は完全一致、`title`/`tags` は類似度比較
- **body**: `difflib.SequenceMatcher` でテキスト全体の類似度を計算

最終スコア = frontmatter スコア × 0.3 + body スコア × 0.7

### Rationale
- frontmatter の構造的正しさ（キー欠落など）は重要だが、body の内容がメインの検証対象
- LLMの揺れは主に body（要約、summary_content）に現れる
- frontmatter の `file_id` は決定的（SHA256ハッシュ）なので完全一致で検証可能

### Alternatives considered
- **全体を1つのテキストとして比較**: frontmatter の構造的問題を見逃す可能性
- **JSON に変換して比較**: Markdown のフォーマットを捨てることになる

## R-3: E2Eテストの実行フロー

### Decision
現在のMakefileの `test-e2e` ターゲットを改修する。

1. Ollama チェック
2. テストデータ準備（`data/test/` にフィクスチャコピー）
3. パイプラインを `format_markdown` まで一括実行（`kedro run --env=test --to-nodes=format_markdown`）
4. 最終出力 (`data/test/07_model_output/notes/*.md`) をゴールデンファイル (`tests/fixtures/golden/*.md`) と比較
5. Python スクリプトで類似度を計算し、90%閾値で判定
6. クリーンアップ

### Rationale
- 既存の `test-e2e` の仕組み（テスト用 data ディレクトリ、env=test）を活用
- 中間チェック（Step 3, 4 の件数確認）を削除し、最終出力の比較に集中
- 比較ロジックは Python スクリプトとして実装し、Makefile から呼び出す

### Alternatives considered
- **unittest として実装**: E2Eテストは Ollama 依存であり、通常の `make test` とは分離すべき
- **シェルスクリプトで diff**: 類似度計算がシェルでは複雑

## R-4: ユニットテスト強化の範囲

### Decision
既存のユニットテストに、出力の基本的な妥当性チェックを追加する。

対象ノードと追加する検証:
- `parse_claude_zip`: 出力が空dict でないこと（既存テストでカバー済み）
- `extract_knowledge`: 出力に `generated_metadata` キーが存在すること、`title` が空文字でないこと（既存テストでカバー済み）
- `generate_metadata`: 出力に `metadata` キーが存在すること（既存テストでカバー済み）
- `format_markdown`: 出力の `content` が空でないこと、frontmatter が存在すること（既存テストでカバー済み）

### Rationale
既存のユニットテストを確認した結果、各ノードの出力非空・必須キー存在・成功状態の検証は**すでにカバーされている**。FR-009 の要件は既存テストで満たされている。

### Alternatives considered
- 追加のユニットテストを書く: 既存で十分なため不要
