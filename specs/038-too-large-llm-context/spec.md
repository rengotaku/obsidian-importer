# Feature Specification: too_large 判定の LLM コンテキストベース化

**Feature Branch**: `038-too-large-llm-context`
**Created**: 2026-01-27
**Status**: Draft
**Input**: User description: "JSONのオーバーヘッドを減らす。too_largeの対象はLLMが処理するテキストのみ"

## 背景

現状の `too_large` 判定は `item.content`（生 JSON 全体）のサイズで行われている。しかし、LLM に渡されるのは会話メッセージの `text` フィールドのみであり、以下の問題がある：

1. **メッセージ本文の重複**: Claude エクスポートでは `text` と `content[0].text` に同じ内容が格納されている
2. **不要なメタデータ**: uuid, timestamps, attachments, files 等が含まれる
3. **JSON 構造オーバーヘッド**: 括弧、キー名、エスケープ文字

実測例：
- `item.content`: 28,371 chars
- 実際の LLM コンテキスト: 10,863 chars
- オーバーヘッド: **61.7%**

結果として、本来処理可能なアイテムが誤って `too_large` としてスキップされている。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 正確な too_large 判定 (Priority: P1)

ユーザーが Claude 会話データをインポートする際、LLM に渡す実際のコンテキストサイズに基づいて `too_large` 判定が行われ、本来処理可能なアイテムがスキップされなくなる。

**Why this priority**: 現状の誤判定により、処理可能なアイテムの多くがスキップされている。この問題を解決することで、インポートの成功率が大幅に向上する。

**Independent Test**: 会話データのインポートを実行し、`too_large` でスキップされるアイテム数が適正になることを確認できる。

**Acceptance Scenarios**:

1. **Given** 25,000 chars 未満の LLM コンテキストを持つ会話（JSON オーバーヘッドにより `item.content` は 25,000 chars 超）, **When** インポートを実行する, **Then** 会話は `too_large` としてスキップされず、正常に処理される
2. **Given** 25,000 chars 以上の LLM コンテキストを持つ会話, **When** インポートを実行する, **Then** 会話は `too_large` としてスキップされる
3. **Given** `--chunk` オプションが有効, **When** 25,000 chars 以上の LLM コンテキストを持つ会話をインポートする, **Then** 会話はチャンク分割されて処理される（従来通り）

---

### User Story 2 - メッセージ content 合計による判定 (Priority: P1)

システムは `item.content` の JSON 全体ではなく、会話メッセージの `text` フィールド合計に基づいて `too_large` 判定を行う。

**Why this priority**: User Story 1 を実現するための技術的基盤であり、同時に実装される。

**Independent Test**: ユニットテストで、同じ会話データに対して旧方式と新方式の判定結果を比較できる。

**Acceptance Scenarios**:

1. **Given** メッセージ `text` 合計が 24,000 chars で `item.content` が 50,000 chars の会話, **When** `too_large` 判定を行う, **Then** 判定結果は「処理可能」となる
2. **Given** メッセージ `text` 合計が 26,000 chars で `item.content` が 30,000 chars の会話, **When** `too_large` 判定を行う, **Then** 判定結果は「too_large」となる

---

### Edge Cases

- メッセージが 0 件の会話の場合、LLM コンテキストはヘッダー部分のみとなり、処理可能と判定される
- `text` フィールドが null または空の場合、そのメッセージは 0 chars としてカウントされる
- マルチモーダルメッセージ（画像、音声プレースホルダー含む）の場合、プレースホルダーテキストがカウントされる

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `too_large` 判定において、`item.content` の JSON 全体サイズではなく、LLM に渡されるコンテキストサイズを使用しなければならない
- **FR-002**: LLM コンテキストサイズは、会話メッセージの `text` フィールド合計 + ヘッダー固定長（約 200 chars）+ ラベルオーバーヘッド（メッセージ数 × 15 chars）で計算しなければならない
- **FR-003**: 閾値（デフォルト 25,000 chars）との比較は、計算された LLM コンテキストサイズに対して行われなければならない
- **FR-004**: `--chunk` オプションが有効な場合、`too_large` 判定をスキップする動作は変更しない
- **FR-005**: 判定ロジックの変更は、既存のユニットテストと互換性を維持しなければならない

### Key Entities

- **ProcessingItem**: 処理対象のアイテム。`content` フィールドに生 JSON を保持
- **Conversation**: パース済みの会話データ。`messages` リストを保持
- **Message**: 個別のメッセージ。`text`（または `content`）フィールドを保持

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `too_large` 判定において、実際の LLM コンテキストサイズと判定に使用されるサイズの差が 10% 以内である
- **SC-002**: 既存テストデータに対して、誤って `too_large` とスキップされていたアイテムの 80% 以上が正常に処理される
- **SC-003**: 処理時間の増加は、判定ロジック変更により 5% 以内に収まる
- **SC-004**: 既存のユニットテストがすべてパスする

## Assumptions

- Claude および ChatGPT エクスポートにおいて、メッセージ本文は `text` フィールド（または同等のフィールド）で取得可能
- ヘッダー固定長（200 chars）およびラベルオーバーヘッド（15 chars/メッセージ）は、実際の `_build_user_message()` 出力と十分に近似する
- 判定時点で conversation オブジェクトまたはメッセージリストにアクセス可能
