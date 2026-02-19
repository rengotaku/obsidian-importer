# Quickstart: ETL ジャンル分類の細分化

**Feature**: 058-refine-genre-classification

## 概要

このガイドでは、ETL パイプラインのジャンル分類を拡張し、「その他」カテゴリを30%以下に削減する実装手順を説明します。

## 前提条件

- Python 3.11+
- Kedro 1.1.1
- プロジェクトの venv がアクティブ

```bash
cd /data/projects/obsidian-importer
source .venv/bin/activate
```

## 実装ステップ

### Step 1: 設定ファイルの更新

`conf/base/parameters.yml` に新ジャンルのキーワードと優先順位を追加します。

```yaml
organize:
  # 優先順位リスト（新規追加）
  genre_priority:
    - ai
    - devops
    - engineer
    - economy
    - business
    - health
    - parenting
    - travel
    - lifestyle
    - daily

  # 既存 + 新ジャンルのキーワード
  genre_keywords:
    # 新ジャンル
    ai:
      - AI
      - 機械学習
      - 深層学習
      - 生成AI
      - プロンプト
      - Claude
      - ChatGPT
      - Stable Diffusion
      - LLM
      - GPT
    devops:
      - インフラ
      - コンテナ
      - クラウド
      - CI/CD
      - サーバー
      - Docker
      - Kubernetes
      - NGINX
      - Terraform
      - AWS
    health:
      - 健康
      - 医療
      - フィットネス
      - 運動
      - 病気
    parenting:
      - 子育て
      - 育児
      - 赤ちゃん
      - 教育
      - 幼児
      - キッザニア
    travel:
      - 旅行
      - 観光
      - ホテル
      - 航空
    lifestyle:
      - 家電
      - 電子レンジ
      - 洗濯機
      - DIY
      - 住居
      - 空気清浄機
    # 既存ジャンル（変更なし）
    engineer:
      - プログラミング
      - アーキテクチャ
      - DevOps
      - フレームワーク
      - API
      - データベース
    business:
      - ビジネス
      - マネジメント
      - リーダーシップ
      - マーケティング
    economy:
      - 経済
      - 投資
      - 金融
      - 市場
    daily:
      - 日常
      - 趣味
      - 雑記
      - 生活
```

### Step 2: classify_genre 関数の更新

`src/obsidian_etl/pipelines/organize/nodes.py` の `classify_genre` 関数を更新します。

**変更点**:
1. 優先順位リストを `params` から取得
2. ジャンル分布のログ出力を追加

```python
# 変更前（ハードコード）
for genre_name in ["engineer", "business", "economy", "daily"]:

# 変更後（設定から取得）
genre_priority = params.get("genre_priority", ["engineer", "business", "economy", "daily"])
for genre_name in genre_priority:
```

### Step 3: テストの更新

`tests/test_organize_files.py` に新ジャンルのテストを追加します。

```python
def test_classify_genre_ai(self):
    """Test AI genre classification."""
    item = {"content": "Claude Code でプログラミング", "metadata": {"tags": []}}
    result = classify_genre({"test": lambda: item}, params)
    self.assertEqual(result["test"]["genre"], "ai")

def test_classify_genre_priority(self):
    """Test priority order when multiple genres match."""
    item = {"content": "AI プログラミング", "metadata": {"tags": []}}
    result = classify_genre({"test": lambda: item}, params)
    # ai > engineer なので ai が選ばれる
    self.assertEqual(result["test"]["genre"], "ai")
```

### Step 4: 検証

```bash
# テスト実行
make test

# パイプライン実行
kedro run --pipeline=organize

# 結果確認
ls data/07_model_output/organized/
# ai/ devops/ engineer/ business/ economy/ health/ parenting/ travel/ lifestyle/ daily/ other/
```

## 検証チェックリスト

- [ ] `make test` が全てパス
- [ ] 新ジャンルフォルダが作成される
- [ ] ログにジャンル分布が出力される
- [ ] 「その他」が30%以下

## トラブルシューティング

### Q: 新ジャンルが認識されない

A: `parameters.yml` の `genre_priority` にジャンル名が含まれているか確認してください。

### Q: 既存テストが失敗する

A: 優先順位の変更により、既存テストの期待値が変わっている可能性があります。テストケースを確認してください。

### Q: パフォーマンスが低下した

A: ジャンル数の増加による影響は軽微です。他の原因を確認してください。
