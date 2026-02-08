# Quickstart: E2Eテスト出力検証

## 前提条件

- Ollama がローカルで起動していること
- `make setup` が完了していること

## ゴールデンファイル初回生成

```bash
# パイプラインを実行し、最終出力をゴールデンファイルとして保存
make test-e2e-update-golden

# 確認
ls tests/fixtures/golden/
# → 3件の .md ファイルが生成される

# リポジトリにコミット
git add tests/fixtures/golden/
git commit -m "feat(test): Add golden files for E2E validation"
```

## E2Eテスト実行

```bash
# ゴールデンファイルとの比較テスト
make test-e2e

# 出力例（成功時）:
# ✅ file1.md: 95.2% similarity (threshold: 90%)
# ✅ file2.md: 92.8% similarity (threshold: 90%)
# ✅ file3.md: 91.5% similarity (threshold: 90%)
# ✅ E2E test passed (3/3 files above 90% threshold)

# 出力例（失敗時）:
# ✅ file1.md: 95.2% similarity
# ❌ file2.md: 78.3% similarity (threshold: 90%)
#    Missing keys: tags
#    Body similarity: 72.1%
# ✅ file3.md: 91.5% similarity
# ❌ E2E test failed (1/3 files below threshold)
```

## ゴールデンファイル更新

LLMモデル変更、プロンプト変更、パイプラインのロジック変更後に実行:

```bash
# 新しいゴールデンファイルで上書き
make test-e2e-update-golden

# 差分を確認
git diff tests/fixtures/golden/

# 問題なければコミット
git add tests/fixtures/golden/
git commit -m "chore(test): Update golden files after LLM model change"
```
