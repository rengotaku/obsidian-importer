# Feature Specification: Summary品質改善

**Feature Branch**: `012-summary-quality`
**Created**: 2026-01-15
**Status**: Draft
**Input**: Claude会話ログのSummary品質改善 - 英語→日本語化、冗長な会話経緯説明→知識抽出型の簡潔な要約へ変換

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Summaryを日本語で即座に理解 (Priority: P1)

ユーザーが以前保存したClaude会話ログを開いたとき、Summaryセクションを見て「このノートは何についてか」を5秒以内に把握できる。

**Why this priority**: ナレッジベースの根本価値は「後で参照して役立つこと」。日本語の会話なのに英語のSummaryでは参照時のコストが高すぎる。

**Independent Test**: 任意の正規化済みノートを開き、Summaryだけを読んで内容を説明できるかを検証

**Acceptance Scenarios**:

1. **Given** 日本語で行われたClaude会話ログ, **When** Summaryを読む, **Then** Summaryは日本語で記述されている
2. **Given** Summary付きのノート, **When** 本文を読まずにSummaryだけを見る, **Then** 「このノートの核心的な知識/結論」が明確に分かる

---

### User Story 2 - 知識として再利用可能な構造 (Priority: P1)

ユーザーがノートを検索・参照するとき、Summaryが「会話の経緯説明」ではなく「抽出された知識」になっていて、即座に活用できる。

**Why this priority**: 「誰が何を言った」ではなく「結局何が分かったか」が重要。知識ベースは知識を蓄積する場所。

**Independent Test**: Summaryの内容をそのままコピーして別の場所で使えるか検証

**Acceptance Scenarios**:

1. **Given** 技術的な質問への回答を含むノート, **When** Summaryを見る, **Then** 技術的結論が箇条書きまたは構造化された形式で提示される
2. **Given** 会話形式のノート, **When** Summaryを見る, **Then** 「Claude said」「User asked」のような会話経緯説明は含まれない

---

### User Story 3 - 簡潔さの維持 (Priority: P2)

Summaryは冗長にならず、3-5行程度の簡潔な形式を維持する。

**Why this priority**: 長すぎるSummaryは読まれない。参照効率を最大化するには簡潔さが重要。

**Independent Test**: Summaryの文字数を計測し、適切な長さに収まっているか検証

**Acceptance Scenarios**:

1. **Given** 任意の正規化済みノート, **When** Summaryの長さを確認, **Then** 500文字以内に収まっている
2. **Given** 複数トピックを含む会話, **When** Summaryを生成, **Then** 最も重要な1-2のポイントに絞られている

---

### Edge Cases

- 会話が日本語と英語混在の場合 → Summaryは会話の主要言語に合わせる（日本語優先）
- 会話に明確な結論がない場合 → 「議論されたトピック」を簡潔に列挙
- 既に英語Summaryがある既存ノート → 再正規化時に日本語へ変換

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Summary生成時、会話の言語に合わせた言語でSummaryを出力すること（日本語会話→日本語Summary）
- **FR-002**: Summaryは「会話の流れ」ではなく「抽出された知識・結論」を記述すること
- **FR-003**: Summaryは箇条書き、表、または構造化された形式で核心情報を提示すること
- **FR-004**: Summaryは500文字以内に収めること
- **FR-005**: 「The user asked」「Claude provided」等の会話経緯表現を使用しないこと
- **FR-006**: 技術的なトピックの場合、具体的な選択肢・推奨事項を明示すること

### Key Entities

- **Summary**: ノートの核心情報を抽出・構造化したセクション。言語は会話に合わせ、形式は知識として再利用可能な構造を持つ
- **会話ログ**: Claudeとの対話記録。Summaryの生成元となるソースデータ
- **正規化済みノート**: frontmatterに`normalized: true`を持ち、Summaryが品質基準を満たすノート

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 正規化後のSummaryを読んで、5秒以内にノートの主題を理解できる
- **SC-002**: 日本語会話のノートにおいて、Summaryが100%日本語で記述されている
- **SC-003**: Summaryに「User asked」「Claude said」等の会話経緯表現が含まれない
- **SC-004**: Summaryの長さが500文字以内である
- **SC-005**: Summaryから会話本文を読まずに、核心的な知識・結論を抽出できる

## Clarifications

### Session 2026-01-15

- Q: Summary Phaseの位置（独立Phase vs 既存Phase拡張） → A: 新規Stage追加（stage5_summaryとして独立定義）

## Assumptions

- 新規 `stage5_summary` を追加し、stage4_metadata の後に実行
- プロンプトファイル `stage5_summary.txt` を新規作成
- `stages.py` に `stage5_summary()` 関数を追加
- `config.py` の `STAGE_PROMPTS` に新規エントリを追加
- `pipeline/runner.py` にstage5呼び出しを追加
- 既存の英語Summaryを持つノートは再正規化時に更新対象となる
- LLMを使用したSummary生成は現行のOllama統合を前提とする
