# Research: Frontmatter ファイル振り分けスクリプト

**Date**: 2026-02-18
**Feature Branch**: `057-frontmatter-file-organizer`

## 1. YAML Frontmatter パース

### Decision
PyYAML の `yaml.safe_load()` を使用して frontmatter を読み取る。

### Rationale
- プロジェクトで既に PyYAML を使用中（既存依存関係）
- `safe_load()` は安全でセキュリティリスクが低い
- 既存の `organize/nodes.py` で同様のパターンを使用

### Alternatives Considered
- **python-frontmatter**: 追加依存関係が必要、却下
- **正規表現**: 複雑な YAML 構造に対応困難、却下
- **ruamel.yaml**: 追加依存関係、却下

## 2. ファイル移動 vs コピー

### Decision
`shutil.move()` を使用してファイルを移動する。

### Rationale
- Issue #21 の要件が「移動」を明示
- ディスク容量の節約
- 元ファイルの重複管理が不要

### Alternatives Considered
- **shutil.copy2()**: メタデータ保持でコピー、ディスク容量増加、却下
- **os.rename()**: 異なるファイルシステム間で失敗する可能性、却下

## 3. フォルダ名の特殊文字置換

### Decision
topic 内の特殊文字 `/\:*?"<>|` をアンダースコア `_` に置換する。

### Rationale
- Windows/macOS/Linux 全てで安全なファイル名
- 情報の損失を最小限に抑える
- 既存の `format_markdown` ノードでも類似パターンを使用

### Alternatives Considered
- **削除**: 情報損失、却下
- **URLエンコード**: 読みにくい、却下
- **ハイフン置換**: アンダースコアの方が既存パターンと一貫性あり

## 4. 設定ファイル形式

### Decision
YAML 形式で `conf/base/genre_mapping.yml` に保存。

### Rationale
- 既存の Kedro 設定構造と一貫性
- 人間が編集しやすい
- PyYAML で読み取り可能

### Sample Configuration

```yaml
# Genre mapping: English key -> Japanese folder name
genre_mapping:
  engineer: エンジニア
  business: ビジネス
  economy: 経済
  daily: 日常
  other: その他

# Default paths (can be overridden via CLI)
default_input: data/07_model_output/organized
default_output: ~/Documents/Obsidian/Vaults
```

## 5. CLI インターフェース

### Decision
argparse で以下のオプションを提供：
- `--dry-run`: プレビューモード
- `--input PATH`: 入力ディレクトリ
- `--output PATH`: 出力ディレクトリ
- `--config PATH`: 設定ファイルパス

### Rationale
- 標準ライブラリのみ使用
- Makefile からの呼び出しが容易
- 既存スクリプトパターンと一貫性

## 6. 既存コードとの関係

### Decision
既存の `organize` パイプラインとは独立したスクリプトとして実装。

### Rationale
- `organize` パイプライン: ETL 内での genre/topic 埋め込み（Kedro）
- 新スクリプト: ETL 処理後のファイル配布（スタンドアロン）
- 役割が明確に異なる

### Integration Point
- 入力: `data/07_model_output/organized/*.md`（organize パイプラインの出力）
- 出力: `~/Documents/Obsidian/Vaults/{genre}/{topic}/`

## 7. エラーハンドリング戦略

### Decision
- 設定ファイル未存在: 即座にエラー終了、セットアップ手順表示
- frontmatter 読み取り失敗: スキップして警告ログ
- 同名ファイル衝突: スキップして警告表示
- フォルダ作成失敗: エラーログ、処理継続

### Rationale
- データ損失防止を最優先
- 部分的な成功を許容（全件失敗を回避）
- 明確なフィードバックで問題特定を支援
