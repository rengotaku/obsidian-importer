# Research: ローカルLLM品質向上

**Date**: 2026-01-11
**Feature**: 003-llm-quality-enhancement

---

## 1. Few-shot Prompting Best Practices for Small LLMs

### Decision
プロンプトに3-5個の具体的なFew-shot例を含め、出力形式を厳密に指定する。

### Rationale
20Bパラメータモデルは指示理解力が限定的なため、抽象的な指示より具体例が効果的。JSONスキーマの厳密な指定により、パース失敗を減らす。

### Key Findings

1. **構造化出力の強制**
   - JSON形式を明示的に指定
   - 各フィールドの型と制約を記述
   - 不正なJSONへのフォールバック処理が必要

2. **日本語タイトル生成の最適化**
   - 「ファイル名として使用される」ことを明示
   - 禁止文字リストを具体的に列挙
   - 良い例・悪い例のペアを提示

3. **コンテンツ改善の指示**
   - 「冗長」「不完全」の具体例を提示
   - 改善前→改善後のペアを3例以上含める
   - コードブロックは保持する指示を明示

### Alternatives Considered
- Zero-shot: 品質が不安定、フォーマット違反多発
- Chain-of-Thought: 小型モデルでは効果薄、トークン消費大

---

## 2. Existing Tag Vocabulary Analysis

### Decision
既存タグから頻度上位100個を抽出し、カテゴリ別に整理してプロンプトに注入する。

### Rationale
タグの一貫性を保つには、既存語彙を参照させることが最も効果的。頻度ベースで重要タグを選別。

### Current Tag Distribution

| カテゴリ | 頻出タグ例 | 件数 |
|---------|-----------|------|
| 言語 | rails, ruby, golang, javascript, nodejs | 100+ |
| インフラ | aws, docker, linux, nginx, kubernetes | 50+ |
| ツール | git, bash, ssh, vim | 30+ |
| 概念 | security, setup, 未解決 | 20+ |
| 日常 | 話し方, 旅行 | 10+ |

### Tag Normalization Rules

1. **大文字小文字の統一**: `AWS` → `aws`, `Linux` → `linux`
2. **表記ゆれの統合**: `docker-compose` と `Docker Compose` → `docker-compose`
3. **自動生成タグの除外**: `conversation`, `claude-export` はプロンプトに含めない

### Implementation
```python
def extract_tag_dictionary(vaults: list[Path]) -> dict[str, list[str]]:
    """各Vaultからタグを抽出し、カテゴリ別に整理"""
    # 頻度カウント
    # 正規化（小文字化、ハイフン統一）
    # 上位100件を抽出
    # カテゴリ別に分類
```

---

## 3. Markdown Normalization Rules

### Decision
LLMではなく正規表現ベースのルールで後処理を行う。確実性と速度を優先。

### Rationale
フォーマット正規化は決定論的なルールで十分対応可能。LLMに任せると不確実性が増す。

### Normalization Rules

| ルール | パターン | 置換 |
|--------|---------|------|
| 空行圧縮 | `\n{3,}` | `\n\n` |
| 見出しレベル調整 | `^# ` → `## ` | 最上位を##に |
| 箇条書き統一 | `^[*+] ` | `- ` |
| 末尾空白削除 | `[ \t]+$` | `` |
| frontmatter保護 | `^---[\s\S]*?---` | 変更なし |

### Implementation Order
1. frontmatter抽出・保護
2. 見出しレベル調整（全体シフト）
3. 箇条書き記号統一
4. 空行圧縮
5. 末尾空白削除
6. frontmatter再結合

---

## 4. English Document Detection Heuristics

### Decision
文書長、見出し構造、英語比率の3指標で判定。閾値超過で「完全な英語文書」と判定。

### Rationale
単純な言語検出では断片的メモと完成文書を区別できない。構造的な完成度も考慮が必要。

### Detection Criteria

| 指標 | 閾値 | 重み |
|------|------|------|
| 文書長 | 500文字以上 | 0.3 |
| 英語比率 | 80%以上 | 0.4 |
| 見出し構造 | 2個以上の見出し | 0.3 |

**判定ロジック**:
- 加重スコア 0.7以上 → 「完全な英語文書」として保持
- 0.7未満 → 日本語化対象

### Implementation
```python
def is_complete_english_document(content: str) -> tuple[bool, float]:
    """完全な英語文書かどうかを判定"""
    length_score = min(len(content) / 500, 1.0) * 0.3
    english_ratio = count_english_chars(content) / len(content)
    english_score = english_ratio * 0.4
    heading_count = len(re.findall(r'^#{1,6} ', content, re.MULTILINE))
    heading_score = min(heading_count / 2, 1.0) * 0.3
    total_score = length_score + english_score + heading_score
    return total_score >= 0.7, total_score
```

---

## 5. Quality Evaluation Methodology

### Decision
サンプルベースの人間評価 + 自動メトリクスのハイブリッド。

### Rationale
品質の主観的側面（読みやすさ、適切さ）は人間評価が必須。ただし全件は非現実的なのでサンプリング。

### Evaluation Framework

#### 自動メトリクス（全件）
- frontmatter完全性: title, tags, created, normalizedの存在
- フォーマット規約準拠: 空行、見出し、箇条書き
- タグ語彙一貫性: 既存タグ辞書との一致率

#### 人間評価（サンプル20件）
- タイトル品質: 1-5スケール（内容を正確に表現しているか）
- タグ適切性: 1-5スケール（過不足なく付与されているか）
- コンテンツ改善: Before/After比較（改善されたか）

### Claude Opus比較手法
1. 同一ファイル10件をClaude OpusとローカルLLMで処理
2. 出力を並べて人間がブラインド評価
3. 勝率・引き分け率を算出
4. 70%同等 = 勝率30%以下 or 引き分け60%以上

---

## Summary: Technical Decisions

| 項目 | 決定 |
|------|------|
| プロンプト設計 | Few-shot 3-5例、JSON形式強制 |
| タグ辞書 | 頻度上位100件、カテゴリ別整理 |
| フォーマット正規化 | 正規表現ベース後処理 |
| 英語文書判定 | 長さ・英語比率・見出し構造の加重スコア |
| 品質評価 | 自動メトリクス + サンプル人間評価 |

---

## Next Steps

1. data-model.md: エンティティ定義
2. contracts/cli.md: CLI仕様
3. quickstart.md: 開発ガイド
