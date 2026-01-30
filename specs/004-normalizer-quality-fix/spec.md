# Feature Specification: Ollama Normalizer 品質改善

**Feature Branch**: `004-normalizer-quality-fix`
**Created**: 2026-01-12
**Status**: Draft
**Input**: テスト結果分析 (TEST_RESULTS_ANALYSIS.md) に基づく品質改善

## 背景

ollama_normalizer.py のfixtureテスト結果（成功率44%）から、以下の品質問題が特定された：

- JSONパースエラーによる処理失敗
- 長文ドキュメントのコンテンツ切り捨て
- 既存frontmatterフィールドの意図しない削除
- タグ数の最小値（3個）未達成
- 見出しレベルの過剰変換

## User Scenarios & Testing *(mandatory)*

### User Story 1 - JSONパースエラー時の自動リカバリ (Priority: P1)

ユーザーが技術文書を正規化しようとした際、LLMがマルフォームドJSONを返しても、システムが自動的にリトライし、処理を完了する。

**Why this priority**: 現在はJSONエラーで処理が完全に失敗し、ユーザーは手動で再実行する必要がある。これは最も深刻な問題であり、処理成功率に直接影響する。

**Independent Test**: tech_document.md fixtureで実行し、JSONエラーが発生しても最終的に正規化結果が得られることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが不正なJSON形式を返した場合、**When** 正規化処理を実行すると、**Then** システムは最大3回までリトライし、有効なJSONが得られれば処理を継続する
2. **Given** 3回のリトライ後もJSONが無効な場合、**When** リトライ上限に達すると、**Then** システムはエラー内容を記録し、ユーザーに具体的なエラーメッセージを表示する
3. **Given** JSONにコードブロック記号（```json）が含まれている場合、**When** パース前処理を行うと、**Then** システムはこれらを自動的に除去してからパースする

---

### User Story 2 - 長文ドキュメントの安全な処理 (Priority: P1)

ユーザーが大きなドキュメント（50KB以上）を正規化する際、コンテンツが失われることなく、メタデータ（タイトル、タグ）のみが更新される。

**Why this priority**: 長文ドキュメントのコンテンツ切り捨ては、ユーザーの重要なデータ損失につながる致命的な問題。

**Independent Test**: long_document.md fixture（116KB）で実行し、元のコンテンツ行数が維持されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 50KB以上のドキュメントが入力された場合、**When** 正規化処理を実行すると、**Then** システムは「軽量モード」で処理し、frontmatterのみを更新する
2. **Given** 軽量モードで処理される場合、**When** 処理が完了すると、**Then** 元のコンテンツ本文は1文字も変更されない
3. **Given** 軽量モードが適用された場合、**When** 処理結果を表示すると、**Then** ユーザーに「軽量モードで処理されました」というメッセージが表示される

---

### User Story 3 - 既存frontmatterフィールドの保持 (Priority: P2)

ユーザーが既にfrontmatterを持つドキュメントを正規化する際、uuid、created、updated などの既存カスタムフィールドが保持される。

**Why this priority**: ユーザー独自のメタデータが失われると、他のツールやワークフローとの連携が壊れる。

**Independent Test**: 既存frontmatterを持つfixtureで実行し、カスタムフィールドが出力に含まれることを確認できる。

**Acceptance Scenarios**:

1. **Given** 既存のfrontmatterにuuid、created、updatedフィールドがある場合、**When** 正規化処理を実行すると、**Then** これらのフィールドは出力に保持される
2. **Given** 既存のタグとシステム生成タグがある場合、**When** 正規化処理を実行すると、**Then** 重複を除去した上で両方のタグがマージされる
3. **Given** normalizedフィールドがfalseまたは未設定の場合、**When** 正規化処理を実行すると、**Then** normalizedフィールドはtrueに更新される

---

### User Story 4 - タグ数の最小値保証 (Priority: P3)

ユーザーがドキュメントを正規化した際、常に3〜5個のタグが付与される。

**Why this priority**: タグ数の一貫性はナレッジベースの検索性に影響するが、致命的な問題ではない。

**Independent Test**: bad_format.md fixtureで実行し、出力に3個以上のタグが含まれることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが2個以下のタグを生成した場合、**When** ポストプロセス処理を行うと、**Then** システムは関連タグを自動追加し、最低3個のタグを保証する
2. **Given** LLMが6個以上のタグを生成した場合、**When** ポストプロセス処理を行うと、**Then** システムは重要度の低いタグを除去し、最大5個に制限する
3. **Given** 自動追加されたタグがある場合、**When** 差分表示を行うと、**Then** ユーザーに「タグを自動追加しました」というメッセージが表示される

---

### User Story 5 - 見出しレベルの適切な変換 (Priority: P3)

ユーザーがドキュメントを正規化した際、見出しレベルの変換は最小限に抑えられる。

**Why this priority**: 見出し構造の過剰な変更は読みやすさに影響するが、データ損失ではない。

**Independent Test**: english_complete.md fixtureで実行し、見出しレベルの変更が1レベルのみであることを確認できる。

**Acceptance Scenarios**:

1. **Given** ドキュメントに`#`見出しがある場合、**When** frontmatter追加後の正規化を行うと、**Then** `#`は`##`に変換されるが、それ以下の見出しはレベルを維持する
2. **Given** ドキュメントに`##`以下の見出しのみがある場合、**When** 正規化処理を実行すると、**Then** 見出しレベルは変更されない

---

### Edge Cases

- 空のドキュメント（0バイト）が入力された場合 → dustとして分類し、@dustフォルダへ移動
- frontmatterのみで本文がないドキュメント → 既存frontmatterを保持し、本文なしのまま処理
- 複数の言語が混在するドキュメントでのタグ言語 → 日本語タグを優先、既存のタグ辞書から選択
- LLMが応答しない（タイムアウト）場合 → 60秒でタイムアウトし、エラーとして記録

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはJSONパースエラー時に最大3回までリトライしなければならない
- **FR-002**: システムはJSON応答からコードブロック記号（```json, ```）を自動除去しなければならない
- **FR-003**: システムは50KB以上のドキュメントを検知し、軽量モードで処理しなければならない
- **FR-004**: 軽量モードでは、frontmatter（タイトル、タグ、ジャンル）のみを更新し、本文は変更してはならない
- **FR-005**: システムは既存frontmatterのカスタムフィールド（uuid、created、updated等）を保持しなければならない
- **FR-006**: システムは出力タグ数を3〜5個の範囲に正規化しなければならない
- **FR-007**: タグが3個未満の場合、システムはtag_dictionary.jsonから関連タグを自動追加しなければならない
- **FR-008**: 見出しレベル変換は`#`→`##`のみとし、それ以下の見出しは変更してはならない
- **FR-009**: システムはリトライ回数、軽量モード適用、タグ自動追加をログに記録しなければならない
- **FR-010**: システムは処理統計（成功率、リトライ率、軽量モード適用率）を`--metrics`で表示できなければならない

### Key Entities

- **ProcessingResult**: 正規化結果（ジャンル、タイトル、タグ、改善点、確信度、処理モード）
- **RetryContext**: リトライ状態（試行回数、エラー内容、最終結果）
- **LightweightMode**: 軽量モード設定（閾値、対象フィールド、適用フラグ）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: fixtureテストの成功率が44%から90%以上に向上する
- **SC-002**: JSONパースエラーによる処理失敗が0件になる（リトライで回復）
- **SC-003**: 50KB以上のドキュメントでコンテンツ損失が0件になる
- **SC-004**: 既存frontmatterフィールドの保持率が100%になる
- **SC-005**: 全ての正規化結果でタグ数が3〜5個の範囲内になる
- **SC-006**: 1ファイルあたりの処理時間が60秒以内（リトライ含む）

## Assumptions

- Ollama APIは常に利用可能で、応答遅延は60秒以内と想定
- tag_dictionary.jsonには十分な数のタグ候補が存在する
- 軽量モードの閾値（50KB）は、LLMのコンテキストウィンドウ制限に基づく妥当な値
- 見出しレベル変換は、Obsidianのfrontmatter仕様に準拠した動作
