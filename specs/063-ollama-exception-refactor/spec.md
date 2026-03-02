# Feature Specification: call_ollama 例外ベースリファクタリング + 汎用ログコンテキスト

**Feature Branch**: `063-ollama-exception-refactor`
**Created**: 2026-03-01
**Status**: Draft
**Input**: Issue#45 - refactor: call_ollama を例外ベースに変更し、呼び出し元で file_id 付きログ出力

## Clarifications

### Session 2026-03-01

- Q: スコープ拡大の方針 → A: 本 Issue でスコープ拡大し、contextvars でプロジェクト全体のログに file_id を自動追加する仕組みを導入
- Q: file_id 設定のタイミング → A: パーティション処理開始時（PartitionedDataset のループ内）で設定
- Q: ログフォーマット → A: `[file_id] メッセージ` 形式（file_id がある場合のみプレフィックス表示）
- Q: 既存の手動ログ出力の扱い → A: 既存の手動 `[{file_id}]` プレフィックスを削除し、フォーマッターに統一
- Q: 例外クラスと contextvars の関係 → A: 例外クラスは情報保持のみ、ログ出力は呼び出し元（contextvars 経由で file_id 自動付与）
- Q: 処理継続と新規コード対応 → A: 例外はキャッチしてデフォルト値で処理継続、新規コードは自動的に file_id 付きログ対応

## 背景

現在の `call_ollama` 関数は `(response, error)` タプルを返す設計になっている。この設計では、エラー発生時のログに処理中のファイルを特定するための `file_id` を含めることが困難。

### 現状の問題

```
WARNING  Empty response from LLM (context_len=1698 chars)    ollama.py:136
```

`ollama.py` 内のログには `file_id` が含まれておらず、問題のあるファイルを特定することが困難。

### 解決アプローチ

1. **Ollama 例外クラス**: エラー種別の識別と詳細情報（context_len 等）の保持
2. **汎用ログコンテキスト**: Python の `contextvars` を使い、パーティション処理単位で file_id をログに自動追加

### 関連 Issue

- #44 (LLM エラーログに file_id を含める)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - エラー発生時のファイル特定 (Priority: P1)

開発者として、パイプライン処理でエラーや警告が発生した際に、どのファイルで問題が起きたかをログから即座に特定できるようにしたい。

**Why this priority**: デバッグ効率に直結する最も重要な改善。エラー発生時にファイルを特定できないと、原因究明に大幅な時間がかかる。

**Independent Test**: エラー発生時のログ出力を確認し、`[file_id]` プレフィックスが自動的に含まれていることを検証できる。

**Acceptance Scenarios**:

1. **Given** パーティション処理中に LLM が空のレスポンスを返した場合、**When** エラーがログに記録されるとき、**Then** ログメッセージに `[file_id]` プレフィックスが自動的に付与される
2. **Given** パーティション処理中に任意の警告が発生した場合、**When** 警告がログに記録されるとき、**Then** ログメッセージに `[file_id]` プレフィックスが自動的に付与される
3. **Given** パーティション処理外でログが出力された場合、**When** ログが記録されるとき、**Then** `[file_id]` プレフィックスは付与されない（空のプレフィックスにならない）

---

### User Story 2 - 例外による明確なエラーハンドリング (Priority: P2)

開発者として、`call_ollama` のエラーを例外として受け取り、適切に処理できるようにしたい。

**Why this priority**: タプル返却よりも例外ベースの方がコードの可読性と保守性が向上する。

**Independent Test**: `call_ollama` が例外をスローし、呼び出し元で適切にキャッチできることを検証できる。

**Acceptance Scenarios**:

1. **Given** LLM が空のレスポンスを返した場合、**When** `call_ollama` が呼ばれるとき、**Then** `OllamaEmptyResponseError` がスローされる
2. **Given** リクエストがタイムアウトした場合、**When** `call_ollama` が呼ばれるとき、**Then** `OllamaTimeoutError` がスローされる
3. **Given** 正常なレスポンスを受け取った場合、**When** `call_ollama` が呼ばれるとき、**Then** レスポンス文字列が返される（例外はスローされない）

---

### User Story 3 - エラー詳細情報の保持 (Priority: P3)

開発者として、例外オブジェクトからエラーの詳細情報（context_len 等）を取得できるようにしたい。

**Why this priority**: デバッグ時の追加情報として有用だが、P1/P2 の機能が動作していれば最低限の目的は達成される。

**Independent Test**: 例外オブジェクトから `context_len` などの属性を取得できることを検証できる。

**Acceptance Scenarios**:

1. **Given** `OllamaEmptyResponseError` がスローされた場合、**When** 例外オブジェクトにアクセスするとき、**Then** `context_len` 属性が取得できる

---

### Edge Cases

- LLM レスポンスが空白文字のみの場合 → `OllamaEmptyResponseError` として扱う
- ネットワーク接続エラーの場合 → 既存の `OllamaConnectionError` を継続使用、または `OllamaError` の派生クラスに統合
- 複数種類のエラーが連続して発生した場合 → 各エラーが個別に `[file_id]` 付きでログに記録される
- パーティション処理外でのログ出力 → `[file_id]` プレフィックスは付与されない（空やN/Aではない）
- vault_output パイプライン → file_id コンテキストが設定されていれば自動的にログに含まれる

## Requirements *(mandatory)*

### Functional Requirements

#### 汎用ログコンテキスト機能

- **FR-001**: システムは `contextvars` を使用してログコンテキスト（file_id）を管理する仕組みを提供しなければならない
- **FR-002**: パーティション処理開始時に file_id がコンテキストに設定されなければならない
- **FR-003**: ログフォーマッターは file_id が設定されている場合のみ `[file_id]` プレフィックスを出力しなければならない
- **FR-004**: 既存の手動 `[{file_id}]` プレフィックス出力をすべて削除しなければならない
- **FR-005**: 新規に追加されるログ出力コードは、パーティション処理内であれば自動的に file_id が付与されなければならない（明示的な対応不要）

#### Ollama 例外クラス

- **FR-006**: システムは `OllamaError` 基底例外クラスを提供しなければならない
- **FR-007**: システムは空レスポンスを表す `OllamaEmptyResponseError` 例外クラスを提供しなければならない
- **FR-008**: システムはタイムアウトを表す `OllamaTimeoutError` 例外クラスを提供しなければならない
- **FR-009**: `call_ollama` 関数はエラー時にタプルではなく例外をスローしなければならない
- **FR-010**: `call_ollama` 関数は成功時にレスポンス文字列のみを返さなければならない
- **FR-011**: 例外クラスは `context_len` 属性を保持しなければならない
- **FR-012**: 呼び出し元は例外をキャッチし、デフォルト値を返して処理を継続しなければならない（パイプライン全体の中断を防ぐ）

#### テスト

- **FR-013**: 既存のテストは新しい例外ベースの設計に対応して更新されなければならない
- **FR-014**: 汎用ログコンテキスト機能に対するユニットテストが追加されなければならない

### Key Entities

- **LogContext**: contextvars ベースのログコンテキスト管理。file_id の設定・取得を提供
- **ContextAwareFormatter**: file_id を自動的にプレフィックスとして追加するカスタムフォーマッター
- **OllamaError**: Ollama API エラーの基底例外クラス。`message` と `context_len` を保持
- **OllamaEmptyResponseError**: LLM が空または空白のみのレスポンスを返した場合の例外
- **OllamaTimeoutError**: リクエストタイムアウト時の例外

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: パーティション処理中のすべてのログに `[file_id]` プレフィックスが自動的に含まれる
- **SC-002**: 既存の手動 `[{file_id}]` プレフィックス出力がすべて削除されている
- **SC-003**: すべての Ollama 呼び出し元が例外ベースのエラーハンドリングに移行している
- **SC-004**: 既存のテストカバレッジが維持される（80%以上）
- **SC-005**: 新しい機能（ログコンテキスト、例外クラス）に対するユニットテストが追加されている
- **SC-006**: 例外発生時もパイプライン処理が継続され、他のパーティションが正常に処理される

## 影響範囲

### 汎用ログコンテキスト

- `src/obsidian_etl/utils/log_context.py` - 新規作成（contextvars 管理）
- `conf/base/logging.yml` - カスタムフォーマッター設定
- すべての nodes.py - パーティション処理開始時に file_id 設定
- `src/obsidian_etl/pipelines/organize/nodes.py` - 手動プレフィックス削除

### Ollama 例外クラス

- `src/obsidian_etl/utils/ollama.py` - 例外クラス追加、`call_ollama` 変更
- `src/obsidian_etl/pipelines/organize/nodes.py` - 3箇所の呼び出し元更新
- `src/obsidian_etl/utils/knowledge_extractor.py` - 2箇所の呼び出し元更新
- 関連テストファイル - 例外ベースのテストに更新

## 設計意図

### 処理継続の保証

例外ベースに変更しても、パイプライン処理は中断しない：

```python
# 変更後のパターン
try:
    response = call_ollama(...)
except OllamaError as e:
    logger.warning(f"Failed: {e}")  # file_id は自動付与
    return "", "other"  # デフォルト値で処理継続
```

1ファイルのエラーが他のパーティション処理に影響を与えない。

### 新規コードの自動対応

contextvars + カスタムフォーマッターにより、新規コードは自動的に file_id 付きログに対応：

```python
# 新規コードで普通にログを書くだけで file_id が付与される
logger.warning("何らかのエラー")
# 出力: [abc123def456] 何らかのエラー
```

パーティション処理のループ内で `set_file_id()` が呼ばれていれば、そのスコープ内のすべてのログに自動的に `[file_id]` が付与される。開発者は明示的に file_id を渡す必要がない。

## 前提条件

- 既存の `call_ollama` 関数のインターフェースを完全に置き換える（後方互換性は維持しない）
- プロジェクト方針「後方互換性は考慮しない」に従う
- Kedro にはノード実行時のログコンテキスト自動注入機能がないため、アプリケーションレベルで実装する
