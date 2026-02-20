# Phase 2 Output

## 作業概要
- Phase 2 - User Story 1 Preview の実装完了
- FAIL テスト 11 件を PASS させた（1つの ImportError で全テストメソッドがブロックされていた）
- organize_preview パイプライン実装完了

## 修正ファイル一覧
- `src/obsidian_etl/pipelines/vault_output/nodes.py` - 新規作成
  - `sanitize_topic()`: トピックを安全なフォルダ名に変換（/ と \ をアンダースコアに置換、空白除去）
  - `resolve_vault_destination()`: frontmatter から genre/topic/title を抽出し、Vault パスを解決
  - `check_conflicts()`: 出力先ファイルの存在確認、競合情報を返す
  - `log_preview_summary()`: 出力先一覧、競合情報、Vault 別ファイル数を集計・ロギング
- `src/obsidian_etl/pipelines/vault_output/pipeline.py` - 新規作成
  - `create_preview_pipeline()`: プレビューパイプラインの定義（3つのノードを連結）
- `src/obsidian_etl/pipeline_registry.py` - 修正
  - `organize_preview` パイプラインを登録

## 実装詳細

### sanitize_topic()
- **目的**: トピック文字列をファイルシステムで安全なフォルダ名に変換
- **変換ルール**:
  - `/` と `\` を `_` に置換
  - 先頭・末尾の空白を除去
  - 空文字列はそのまま返す
  - Unicode（日本語）はそのまま保持

### resolve_vault_destination()
- **目的**: ジャンル分類済みファイルの Vault 出力先を解決
- **処理フロー**:
  1. frontmatter をパース（PyYAML 使用）
  2. genre を genre_vault_mapping で Vault 名に変換
  3. topic をサニタイズしてサブフォルダ名に使用
  4. title をファイル名に使用
  5. 完全パスを構築: `{vault_base_path}/{vault_name}/{topic}/{title}.md`
- **エッジケース**:
  - topic が空の場合: Vault 直下に配置
  - genre が未登録の場合: デフォルト Vault "その他" にマッピング

### check_conflicts()
- **目的**: 出力先パスに既存ファイルが存在するか確認
- **返り値**: ConflictInfo リスト（競合があるファイルのみ）
  - `source_file`: 元ファイルの partition_key
  - `destination`: 出力先フルパス
  - `conflict_type`: "exists"
  - `existing_size`: 既存ファイルサイズ
  - `existing_mtime`: 既存ファイル更新日時

### log_preview_summary()
- **目的**: プレビュー情報をロギングし、サマリー dict を返す
- **ロギング内容**:
  - 総ファイル数
  - 競合数
  - Vault 別ファイル数分布
  - 競合ファイル一覧（最大10件まで表示）
- **返り値**:
  - `total_files`: 総ファイル数
  - `total_conflicts`: 競合数
  - `vault_distribution`: dict[Vault名, ファイル数]

## テスト結果

```
Ran 414 tests in 5.567s

OK
```

- **全テスト PASS**: 414 件（Phase 2 で追加された 11 件含む）
- **リグレッションなし**: 既存テストへの影響なし

## 注意点
- **organize_preview パイプライン実行には organized_files データセットが必要**
  - 前段の organize パイプラインを実行してから organize_preview を実行する
  - または、data/07_model_output/organized/ に Markdown ファイルを配置する
- **競合検出は読み取り専用**
  - ファイルコピーは Phase 3 以降で実装
  - 現段階では出力先確認と競合検出のみ

## 次 Phase への引き継ぎ
- **Phase 3 (User Story 2+3 - Vault へのコピー)** で実装予定:
  - `copy_to_vault()`: 実際のファイルコピー処理
  - `log_copy_summary()`: コピー結果のサマリー
  - conflict_handling パラメータに基づくスキップ処理（デフォルト動作）
- **organize_preview パイプラインは独立して動作可能**
  - `kedro run --pipeline=organize_preview` で出力先プレビューを確認できる

## 実装のミス・課題
- **なし**: すべてのテストが PASS し、要件を満たしている
