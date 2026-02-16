# Phase 3 Output

## 作業概要
- Phase 3 - 圧縮率検証共通処理 (User Story 2) の実装完了
- FAIL テスト 9 件を PASS させた (GREEN)
- `compression_validator.py` ユーティリティモジュールを新規作成

## 修正ファイル一覧
- `src/obsidian_etl/utils/compression_validator.py` - 新規作成
  - `CompressionResult` dataclass: 圧縮率検証結果を保持
  - `get_threshold()`: 元サイズに応じたしきい値を返す (10%, 15%, 20%)
  - `validate_compression()`: 圧縮率を検証し、結果を返す

## 実装内容

### CompressionResult dataclass
圧縮率検証結果を保持する dataclass:
- `original_size`: 元コンテンツのサイズ (文字数)
- `output_size`: 出力コンテンツのサイズ (frontmatter 含む)
- `body_size`: 本文サイズ (frontmatter 除く)
- `ratio`: 出力/元のサイズ比
- `body_ratio`: 本文/元のサイズ比
- `threshold`: 適用されたしきい値
- `is_valid`: 圧縮率が基準を満たすか
- `node_name`: 処理ノード名

### get_threshold()
元サイズに応じたしきい値を返す:
- 10,000文字以上: 0.10 (10%)
- 5,000-9,999文字: 0.15 (15%)
- 5,000文字未満: 0.20 (20%)

### validate_compression()
圧縮率を検証:
- `original_content`, `output_content`, `body_content` (オプション), `node_name` を受け取る
- `body_content` が `None` の場合、`output_size` を `body_size` として使用
- `original_size == 0` の場合、ゼロ除算を回避して `is_valid=True` を返す
- `body_ratio >= threshold` で `is_valid` を判定

## テスト結果
```
Ran 304 tests in 0.815s

OK (PASS: 304)
```

全テストが PASS (GREEN) を達成。レグレッションなし。

## 注意点
- `compression_validator.py` は全 transform node で共通利用可能
- Phase 4 で `extract_knowledge` node に統合予定
- Phase 5 で `format_markdown` node のレビューフォルダ出力に使用予定

## 実装のミス・課題
特になし。

## 次 Phase への引き継ぎ
- Phase 4: `extract_knowledge` node に圧縮率検証を統合
- 基準未達アイテムに `review_reason` フラグを追加
- 警告ログを出力
