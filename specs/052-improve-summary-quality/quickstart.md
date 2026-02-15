# Quickstart: LLM まとめ品質の向上

## 概要

このドキュメントは、LLM まとめ品質向上機能の統合シナリオと使用方法を説明します。

## 前提条件

- Python 3.11+
- Ollama がローカルで起動中
- Kedro パイプラインがセットアップ済み

## 統合シナリオ

### シナリオ 1: プロンプト改善の検証

```bash
# 1. テストデータを配置
cp tests/fixtures/claude_test.zip data/01_raw/claude/

# 2. パイプライン実行
kedro run --pipeline=import_claude --params='{"import.limit": 5}'

# 3. 出力を確認
ls data/07_model_output/notes/
ls data/07_model_output/review/

# 4. review フォルダが空または少数であれば成功
```

### シナリオ 2: ゴールデンファイル E2E テスト

```bash
# 1. E2E テスト実行
make test-e2e

# 2. 結果確認
# - 全ゴールデンファイルが圧縮率しきい値を満たす
# - 表形式データが保持されている
```

### シナリオ 3: 手動品質検証

```bash
# 1. review フォルダのファイルを確認
cat data/07_model_output/review/千葉のSwitch2販売実績.md

# 2. frontmatter の review_reason を確認
# review_reason: "extract_knowledge: body_ratio=10.3% < threshold=20.0%"

# 3. 再処理（プロンプト改善後）
kedro run --pipeline=import_claude --from-nodes=extract_knowledge
```

## 検証ポイント

### 圧縮率

| 元サイズ | しきい値 | 検証方法 |
|---------|---------|---------|
| <5000文字 | 20%以上 | frontmatter の review_reason 確認 |
| 5000-9999文字 | 15%以上 | 同上 |
| ≥10000文字 | 10%以上 | 同上 |

### 構造保持

| 元の形式 | 期待される出力 | 検証方法 |
|---------|---------------|---------|
| 表形式 | Markdown テーブル | 目視確認 |
| リスト | 箇条書き | 目視確認 |
| コード | コードブロック | 目視確認 |

## トラブルシューティング

### 圧縮率が改善されない

1. プロンプトが正しく更新されているか確認
   ```bash
   cat src/obsidian_etl/utils/prompts/knowledge_extraction.txt
   ```

2. Ollama モデルが応答しているか確認
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. タイムアウト設定を確認
   ```bash
   grep timeout conf/base/parameters.yml
   ```

### テストが失敗する

1. ゴールデンファイルが存在するか確認
   ```bash
   ls tests/fixtures/golden/
   ```

2. ゴールデンファイルを再生成
   ```bash
   make test-e2e-update-golden
   ```
