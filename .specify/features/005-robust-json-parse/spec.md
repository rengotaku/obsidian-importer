# Feature Specification: Robust JSON Parsing for LLM Responses

**Feature Branch**: `005-robust-json-parse`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Implement robust JSON parsing for LLM responses with bracket balancing and code block extraction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic JSON Extraction (Priority: P1)

ユーザーがファイルを正規化処理する際、LLMが余分なテキストを含むJSON応答を返しても、システムは正しくJSONを抽出して処理を完了する。

**Why this priority**: 現在、LLMが余分なテキストを付加した場合に処理が完全に失敗する。最も頻度が高く、影響が大きい問題。

**Independent Test**: 1つのファイルを処理し、意図的に余分なテキストを含むLLM応答でも正しく処理されることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが `{"genre": "エンジニア"} 補足説明です` と応答した, **When** JSONパース処理が実行される, **Then** `{"genre": "エンジニア"}` のみが抽出され処理が成功する
2. **Given** LLMが `以下がJSONです: {"genre": "ビジネス"}` と応答した, **When** JSONパース処理が実行される, **Then** JSONオブジェクト部分のみが抽出される

---

### User Story 2 - Code Block JSON Extraction (Priority: P1)

LLMがMarkdownコードブロック内にJSONを出力した場合、システムはコードブロックからJSONを優先的に抽出する。

**Why this priority**: LLMはしばしばコードブロック形式でJSONを返す。これは期待される動作であり、正しく処理すべき。

**Independent Test**: コードブロック形式のJSON応答を処理し、正しく抽出されることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが ` ```json {"genre": "経済"} ``` ` 形式で応答した, **When** JSONパース処理が実行される, **Then** コードブロック内のJSONが抽出される
2. **Given** LLMが ` ```{"genre": "日常"}``` ` (jsonラベルなし)で応答した, **When** JSONパース処理が実行される, **Then** コードブロック内のJSONが抽出される

---

### User Story 3 - Nested JSON Handling (Priority: P2)

LLMがネストしたJSONオブジェクトを返した場合、システムは括弧のバランスを正しく追跡し、完全なJSONを抽出する。

**Why this priority**: frontmatterやnormalized_contentを含むJSONは複数レベルのネストを持つ。これを正しく処理できないと機能しない。

**Independent Test**: ネストしたJSONを含む応答を処理し、全体が正しく抽出されることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが `{"frontmatter": {"title": "Test", "tags": ["a", "b"]}}` と応答した, **When** JSONパース処理が実行される, **Then** 完全なネストしたJSONが抽出される
2. **Given** LLMがネストしたJSON後に説明文を付加した, **When** JSONパース処理が実行される, **Then** JSONのみが抽出され説明文は除外される

---

### User Story 4 - Escaped Characters in Strings (Priority: P2)

JSON文字列内にエスケープされた括弧や引用符が含まれている場合、システムは正しくパースする。

**Why this priority**: normalized_contentにはMarkdownコードブロックや特殊文字が含まれることが多い。

**Independent Test**: 文字列内にエスケープ文字を含むJSONを処理し、正しくパースされることを確認できる。

**Acceptance Scenarios**:

1. **Given** LLMが `{"content": "Use } for closing"}` と応答した, **When** JSONパース処理が実行される, **Then** 文字列内の `}` はJSON終端として扱われない
2. **Given** LLMが `{"content": "Say \"Hello\""}` と応答した, **When** JSONパース処理が実行される, **Then** エスケープされた引用符は正しく処理される

---

### Edge Cases

- LLMが空の応答を返した場合は、明確なエラーメッセージを返す
- LLMがJSONを全く含まない応答を返した場合は、「JSON形式の応答がありません」エラーを返す
- LLMが複数のJSONオブジェクトを返した場合は、最初の完全なJSONのみを抽出する
- LLMが不完全なJSON（閉じ括弧なし）を返した場合は、パースエラーを返す
- 極端に長いJSON文字列（10MB以上）はタイムアウト防止のため制限する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはMarkdownコードブロック（` ```json ``` ` または ` ``` ``` `）内のJSONを優先的に抽出しなければならない
- **FR-002**: システムはコードブロックが見つからない場合、括弧バランス追跡で最初の完全なJSONオブジェクトを抽出しなければならない
- **FR-003**: システムはJSON文字列内のエスケープ文字（`\"`, `\\`）を正しく処理しなければならない
- **FR-004**: システムはJSON文字列内の括弧（`{`, `}`）をJSON構造として扱ってはならない
- **FR-005**: システムは複数のJSONオブジェクトが連結されている場合、最初の完全なオブジェクトのみを抽出しなければならない
- **FR-006**: システムはパース失敗時に、エラー位置と周辺コンテキストを含むエラーメッセージを返さなければならない
- **FR-007**: システムはJSONが見つからない場合、明確なエラーメッセージ「JSON形式の応答がありません」を返さなければならない

### Key Entities

- **RawResponse**: LLMからの生の応答テキスト。コードブロック、余分なテキスト、JSONを含む可能性がある
- **ExtractedJSON**: RawResponseから抽出された純粋なJSON文字列
- **ParsedResult**: 抽出されたJSONをパースした辞書オブジェクト
- **ParseError**: パース失敗時のエラー情報（エラー種別、位置、コンテキスト）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 現在失敗しているtech_document.mdのテストケースが成功する
- **SC-002**: 余分なテキストを含むLLM応答の95%以上が正しくパースされる
- **SC-003**: コードブロック形式のJSON応答の100%が正しく抽出される
- **SC-004**: ネストしたJSON（3レベル以上）が正しくパースされる
- **SC-005**: パース処理時間が1応答あたり10ms未満である

## Assumptions

- LLMは常に少なくとも1つの有効なJSONオブジェクトを応答に含む（応答が空でない限り）
- JSONオブジェクトは必ず `{` で始まり `}` で終わる（配列トップレベルは想定しない）
- コードブロック内のJSONはコードブロック外のJSONより信頼性が高い
- パフォーマンス要件として、通常のLLM応答（10KB未満）は即座に処理される
