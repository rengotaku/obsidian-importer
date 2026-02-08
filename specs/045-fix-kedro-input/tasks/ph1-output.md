# Phase 1 Output

## 作業概要

Phase 1 (Setup) を完了。既存コードの全面的な読み込みと BinaryDataset の作成を実施。

## 修正ファイル一覧

- `src/obsidian_etl/datasets/__init__.py` - 新規作成: BinaryDataset のエクスポート
- `src/obsidian_etl/datasets/binary_dataset.py` - 新規作成: AbstractDataset サブクラス (load/save/describe)

## 既存コードの確認結果

### Extract ノードの現状

| Provider | 関数名 | 入力型 | ZIP 対応 |
|----------|--------|--------|----------|
| Claude | `parse_claude_json` | `list[dict]` | 未対応（Phase 2 で変更） |
| OpenAI | `parse_chatgpt_zip` | `dict[str, Callable]` | 対応済み |
| GitHub | `clone_github_repo` | `str` (URL) | N/A（git clone 方式） |

### カタログの現状

- Claude: `json.JSONDataset` + `.json` suffix → Phase 2 で `BinaryDataset` + `.zip` に変更
- OpenAI: `json.JSONDataset` + `.json` suffix → Phase 2 で `BinaryDataset` + `.zip` に変更
- GitHub: `text.TextDataset` + `.md` suffix → Phase 3 でカタログから削除（MemoryDataset へ）

### テストの現状

- 115 テスト PASS（関連テストのみ。RAG テストは pre-existing failures で無関係）
- Claude テスト: `parse_claude_json` を直接呼び出し（list[dict] 入力）
- OpenAI テスト: `parse_chatgpt_zip` を ZIP bytes 入力でテスト（パターン参照可能）
- GitHub テスト: subprocess mock で git clone テスト
- 統合テスト: SequentialRunner + MemoryDataset で E2E テスト

### Pipeline Registry の現状

- `import_claude`, `import_openai`, `import_github` の3パイプラインを登録
- `__default__` = `import_claude`（固定）
- Phase 4 で OmegaConf dispatch に変更予定

## 注意点

- RAG テスト (3 failures, 22 errors) は pre-existing で本フィーチャーと無関係
- OpenAI の `parse_chatgpt_zip` が ZIP 入力パターンの参照実装として利用可能
- テストフィクスチャ `tests/fixtures/claude_test.zip` と `openai_test.zip` は既に存在

## 実装のミス・課題

- なし。Phase 1 は読み込みと軽量な新規ファイル作成のみ。
