# Research: Summary品質改善

**Date**: 2026-01-15
**Feature**: 012-summary-quality

## Research Topics

### 1. 新規Stage追加のパターン

**Question**: 既存パイプラインに新規Stageを追加する際の変更箇所は？

**Findings**:

既存Stage実装パターンを分析した結果、以下の変更が必要:

1. **config.py**: `STAGE_PROMPTS` dictに新規エントリ追加
2. **models.py**: `Stage5Result` TypedDict追加
3. **stages.py**: `stage5_summary()` 関数追加
4. **runner.py**: パイプラインにstage5呼び出し追加

**Decision**: 既存パターンに従い、Stage 5として独立実装

**Rationale**: 責務分離が明確になり、テスト・デバッグが容易

---

### 2. 知識抽出型Summaryのプロンプト設計

**Question**: LLMに「会話経緯」ではなく「知識抽出」をさせるプロンプト設計のベストプラクティスは？

**Findings**:

1. **否定形指示が効果的**: 「〜しない」という明確な禁止事項
   - 「"The user asked", "Claude said" などの会話経緯表現を使用しない」
   - 「会話の流れを説明しない」

2. **出力形式の明示**: 箇条書き・構造化の例示
   - Good example / Bad example を示すと効果的
   - 出力サンプルを提示

3. **役割設定**: 「会話を要約するAI」ではなく「知識を抽出するAI」
   - 「あなたはナレッジベースキュレーターです」

**Decision**: 否定形指示 + Good/Bad example + 役割設定を組み合わせたプロンプト

**Rationale**: 明確な指示と例示でLLMの出力品質を向上

---

### 3. Stage 5 の入出力設計

**Question**: Stage 5 は何を入力とし、何を出力するか？

**Findings**:

- **入力**: Stage 3 の `normalized_content`（Summaryセクションを含む）
- **出力**: 改善された `normalized_content`（Summaryセクションのみ変更）

Stage 5 は以下を行う:
1. `normalized_content` から `## Summary` セクションを抽出
2. Summaryが存在する場合のみLLM呼び出し
3. 改善されたSummaryで `normalized_content` を更新

**Decision**: Summaryセクションのみを対象とし、他のコンテンツは保持

**Rationale**:
- 最小限の変更で既存パイプラインに統合可能
- Summaryがない場合はスキップ（不要なAPI呼び出し回避）

---

### 4. Summary言語判定

**Question**: 会話言語に基づくSummary言語の決定方法は？

**Findings**:

既存パイプラインで `is_english` フラグが各Stageに渡されている。Stage 5 でも同様に活用可能。

**Decision**: 既存の `is_english` フラグを活用

**Rationale**: コード変更最小限、一貫性維持

---

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| Stage追加パターン | config, models, stages, runner の4ファイル変更 |
| プロンプト設計 | 否定形指示 + Good/Bad example + 役割設定 |
| 入出力設計 | normalized_content → Summaryセクションのみ改善 |
| 言語判定 | 既存 is_english フラグ活用 |

## Next Steps

1. `stage5_summary.txt` プロンプト作成
2. `models.py` に `Stage5Result` 追加
3. `stages.py` に `stage5_summary()` 実装
4. `config.py` に `STAGE_PROMPTS` エントリ追加
5. `runner.py` にstage5呼び出し追加
6. テスト作成・実行
