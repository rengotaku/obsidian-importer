# Research: Normalizer Pipeline統合

**Feature**: 014-pipeline-consolidation
**Date**: 2026-01-15

## OQ-001: gpt-oss:20bコンテキスト長サポート

### Decision
`num_ctx: 16384` を使用する

### Rationale
- `ollama show gpt-oss:20b`の結果: `context length: 131072` (128K)
- 16384は十分にサポート範囲内
- デフォルト4096からの4倍拡張で長文ドキュメント対応可能

### Alternatives Considered
- 32768: 過剰（現在の処理対象ファイルサイズに対して）
- 8192: 十分だが、将来の拡張性を考慮して16384を選択

### Implementation
```python
# io/ollama.py 内
options = {"num_ctx": 16384}
```

---

## R-001: Stage A プロンプト設計

### Decision
Dust判定とジャンル分類を1プロンプトで実行

### Rationale
- 両判定は内容理解に基づくため、1回の読み取りで同時実行可能
- `is_dust=true`の場合は他フィールドを省略可能
- JSON出力形式で構造化された結果を返す

### Output Schema
```json
{
  "genre": "エンジニア" | "ビジネス" | "経済" | "日常" | "その他" | "dust" | "unknown",
  "subfolder": "aws" | "",
  "confidence": "high" | "low",
  "reason": "判定理由"
}
```

### Prompt Strategy
- 最初にDust判定（価値あり/なし）
- 価値ありの場合のみジャンル・サブフォルダ判定

### Routing Rules
- `genre: "dust"` → @dust/ フォルダ
- `genre: "unknown"` → @review/ フォルダ（手動レビュー待ち）
- それ以外 → 対応Vault/subfolder

---

## R-002: Stage C プロンプト設計

### Decision
title、tags、summary、relatedを1プロンプトで生成

### Rationale
- 全てメタデータ生成タスク
- コンテンツ理解は1回で十分
- summaryをfrontmatterプロパティとして出力

### Output Schema
```json
{
  "title": "EFSとEBSの違い",
  "tags": ["aws", "storage", "efs"],
  "summary": "AWSのストレージサービスEFSとEBSの違いを解説。",
  "related": ["[[S3]]", "[[EC2]]"]
}
```

### Prompt Strategy
- タイトル: ファイル名として使用可能な形式
- タグ: 3-5個、frontmatter用
- summary: **最大200文字**、Dataview用
- related: 内部リンク形式、最大5件

---

## R-003: 既存テスト構造の流用

### Decision
既存の`normalizer/tests/`構造を維持し、Stage A/B/C用にテストケースを追加

### Rationale
既存テストは**プロパティ毎チェック形式**で変更に強い設計になっている:
- LLM呼び出しはモック化（`@patch`使用）
- 各プロパティを個別にアサート（`result["data"]["genre"]`等）
- デグレーション検知可能（プロパティ値の変化を検出）

```python
# 既存テストパターン例
def test_genre_classification(self, mock_load_prompt, mock_call_llm):
    mock_call_llm.return_value = ('{"genre": "エンジニア", ...}', None)
    result = stage2_genre(...)

    # プロパティ毎チェック
    self.assertTrue(result["success"])
    self.assertEqual(result["data"]["genre"], "エンジニア")
    self.assertEqual(result["data"]["confidence"], 0.85)
```

### Implementation
- `test_pipeline.py`: `test_stage_a_*`, `test_stage_c_*`を追加
- fixtures/: 必要に応じてテストデータ追加
- 既存の`test_stage1_*`、`test_stage2_*`等は削除または非推奨化
- **プロパティ毎チェック形式を維持**してデグレ検知を担保

---

## R-004: 後方互換性

### Decision
旧Stage 1-5関数は削除し、新Stage A/B/Cに完全移行

### Rationale
- 内部APIのため後方互換性維持は不要
- 旧関数を残すと混乱の原因
- テストも新ステージに完全移行

### Migration
1. 新ステージ関数を追加
2. runner.pyを新パイプラインに更新
3. 旧ステージ関数を削除
4. テストを更新
