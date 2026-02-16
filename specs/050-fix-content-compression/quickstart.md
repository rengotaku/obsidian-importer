# Quickstart: 050-fix-content-compression

## 概要

Transform パイプラインの出力コンテンツ圧縮率を改善し、情報欠落を防止する。

## 前提条件

- Python 3.11+
- Kedro 1.1.1
- Ollama が起動していること

## セットアップ

```bash
# Feature ブランチに切り替え
git checkout 050-fix-content-compression

# 依存関係インストール
make setup

# テスト実行
make test
```

## 主な変更点

### 1. プロンプト改善

`src/obsidian_etl/utils/prompts/knowledge_extraction.txt` に情報量目安を追加。

### 2. 圧縮率検証

新規ファイル `src/obsidian_etl/utils/compression_validator.py`:

```python
from obsidian_etl.utils.compression_validator import validate_compression

result = validate_compression(
    original_content="...",
    output_content="...",
    body_content="...",
    node_name="extract_knowledge",
)
if not result.is_valid:
    # review フォルダに出力
```

### 3. レビューフォルダ

基準未達ファイルは `data/07_model_output/review/` に出力。

frontmatter に `review_reason` フィールドが追加される:

```yaml
review_reason: "extract_knowledge: body_ratio=3.8% < threshold=10.0%"
```

## 検証方法

### 圧縮率の確認

```bash
# 圧縮率一覧を表示
python3 << 'EOF'
import os, json, yaml, re

organized_dir = "data/07_model_output/organized"
parsed_dir = "data/02_intermediate/parsed"

for md_file in os.listdir(organized_dir)[:10]:
    if not md_file.endswith('.md'):
        continue
    # ... (圧縮率計算ロジック)
EOF
```

### テスト実行

```bash
# ユニットテスト
make test

# E2E テスト
make test-e2e
```

## 成功基準

- Body% < 5% のファイル数: 30件 → 5件以下
- 平均 Body%: 30.5% → 50%以上
- コードブロック保持率: 90%以上
