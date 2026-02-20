# Research: ETL ジャンル分類の細分化

**Date**: 2026-02-19
**Feature**: 058-refine-genre-classification

## 1. 既存実装の分析

### classify_genre 関数の現状

**場所**: `src/obsidian_etl/pipelines/organize/nodes.py:57-175`

**現在のロジック**:
1. タグからキーワードマッチング（優先）
2. コンテンツからキーワードマッチング
3. first match wins（最初にマッチしたジャンルを採用）
4. マッチなし → "other"

**現在の優先順位（ハードコード）**:
```python
for genre_name in ["engineer", "business", "economy", "daily"]:
```

**問題点**:
- 優先順位がハードコードされている
- 新ジャンル追加には関数修正が必要
- ジャンル分布のログ出力がない

### parameters.yml の現状

**場所**: `conf/base/parameters.yml:61-85`

```yaml
organize:
  genre_keywords:
    engineer: [プログラミング, アーキテクチャ, DevOps, フレームワーク, API, データベース]
    business: [ビジネス, マネジメント, リーダーシップ, マーケティング]
    economy: [経済, 投資, 金融, 市場]
    daily: [日常, 趣味, 雑記, 生活]
```

**改善点**:
- 優先順位リストを追加（設定可能に）
- 新ジャンルのキーワードを追加

## 2. 新ジャンルのキーワード設計

### 決定事項

各新ジャンルに対して、日本語・英語の両方でキーワードを定義する。

| ジャンル | 日本語キーワード | 英語キーワード |
|---------|-----------------|----------------|
| ai | AI, 機械学習, 深層学習, 生成AI, プロンプト | Claude, ChatGPT, Stable Diffusion, LLM, GPT |
| devops | インフラ, コンテナ, クラウド, CI/CD, サーバー | Docker, Kubernetes, NGINX, Terraform, AWS |
| health | 健康, 医療, フィットネス, 運動, 病気 | - |
| parenting | 子育て, 育児, 赤ちゃん, 教育, 幼児 | キッザニア |
| travel | 旅行, 観光, ホテル, 航空 | - |
| lifestyle | 家電, 電子レンジ, 洗濯機, DIY, 住居 | - |

### 根拠

- **ai**: 「その他」に含まれる AI/ML コンテンツ（Stable Diffusion, Claude Code 等）を捕捉
- **devops**: インフラ系（Cloudflare, NGINX, Docker 等）を engineer から分離
- **health**: 健康・医療系を daily から分離
- **parenting**: 子育て系（赤ちゃん連れ旅行, キッザニア 等）を travel/daily から分離
- **travel**: 旅行系（宮崎への旅行 等）を daily から分離
- **lifestyle**: 家電・生活用品（空気清浄機, 電子レンジ 等）を daily から分離

## 3. 優先順位の設計

### 決定事項

```yaml
genre_priority:
  - ai        # AI/ML 系は最優先（engineer に吸収されないように）
  - devops    # インフラ系も優先（engineer より細かく）
  - engineer  # 一般的な技術
  - economy   # 経済・金融
  - business  # ビジネス・マネジメント
  - health    # 健康・医療
  - parenting # 子育て・育児
  - travel    # 旅行
  - lifestyle # 家電・生活
  - daily     # 日記・雑記
  # other は優先順位リストに含めない（デフォルト）
```

### 根拠

1. **ai > devops > engineer**: 専門的なトピックが汎用カテゴリに吸収されるのを防ぐ
2. **economy, business**: ビジネス・経済は明確なカテゴリ
3. **health > parenting > travel > lifestyle > daily**: 生活系は具体的なものから抽象的なものへ

## 4. 実装アプローチ

### 決定事項

**アプローチ**: 既存の `classify_genre` 関数を拡張

**変更点**:
1. ハードコードされた優先順位リストを `params` から取得
2. ジャンル分布のログ出力を追加

### 代替案（却下）

| 代替案 | 却下理由 |
|--------|----------|
| 新関数を作成 | 既存コードの重複、保守性低下 |
| LLM ベースの分類 | 要件外（キーワードマッチングを維持） |
| マルチラベル分類 | 仕様で却下済み（シンプルさ優先） |

## 5. テスト戦略

### 決定事項

1. **ユニットテスト**: 各新ジャンルのキーワードマッチングを検証
2. **優先順位テスト**: 複数ジャンルにマッチする場合の動作確認
3. **既存テスト**: 既存4ジャンルの分類が維持されることを確認

### テストケース例

```python
# ai ジャンルのテスト
{"content": "Claude Code でプログラミング", "expected": "ai"}  # ai > engineer

# devops ジャンルのテスト
{"content": "Docker コンテナの設定", "expected": "devops"}  # devops > engineer

# 複合ケース
{"content": "AI 投資の最新トレンド", "expected": "ai"}  # ai > economy
```

## 6. 移行・互換性

### 決定事項

- 既存の4ジャンル（engineer, business, economy, daily）のキーワードは変更しない
- 新ジャンルで捕捉されるべきファイルが既存ジャンルから移動することは許容
- 既存テストは更新が必要（優先順位変更の影響）

### 影響範囲

| 既存ジャンル | 影響 |
|-------------|------|
| engineer | 一部が ai, devops に移動 |
| daily | 一部が health, parenting, travel, lifestyle に移動 |
| business | 影響なし |
| economy | 影響なし |
