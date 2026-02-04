# Feature Specification: Python Lint Hook

**Feature Branch**: `029-python-lint-hook`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "python lintを導入したい。ClaudeCodeのhookでpythonコードが修正されたら自動実行させたい"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Python コード修正時の自動 Lint (Priority: P1)

開発者として、Claude Code で Python ファイルを編集した際に、lint チェックが自動で実行され、コード品質の問題があればすぐに通知を受けたい。これにより、コーディング中にリアルタイムでフィードバックを得られ、後から大量のエラーに対処する手間を省ける。

**Why this priority**: コア機能。この機能が動作しないと、他のすべての価値が提供されない。

**Independent Test**: Python ファイルを Claude Code で編集し、lint 結果が表示されることを確認する。

**Acceptance Scenarios**:

1. **Given** Claude Code セッションが開始されている状態で、**When** Python ファイル（`.py`）を Edit ツールで修正した時、**Then** lint チェックが自動実行され、問題があれば Claude に結果がフィードバックされる
2. **Given** lint エラーが検出された状態で、**When** Claude がそのエラーを確認した時、**Then** エラーの内容と該当行番号が明確に表示される
3. **Given** Python 以外のファイル（`.md`, `.json` 等）を編集した状態で、**When** ファイルを保存した時、**Then** lint は実行されない

---

### User Story 2 - Lint 問題の修正支援 (Priority: P2)

開発者として、lint で検出された問題を Claude が自動的に認識し、修正提案または自動修正を行ってほしい。これにより、lint エラーの手動修正の手間が省ける。

**Why this priority**: P1 の lint 実行があって初めて価値を発揮する補助機能。

**Independent Test**: lint エラーが検出された Python ファイルに対して、Claude が修正提案を行うことを確認する。

**Acceptance Scenarios**:

1. **Given** lint がエラーを検出した状態で、**When** Claude がエラー内容を分析した時、**Then** 自動修正可能なエラー（フォーマット、未使用インポート等）は自動修正オプションを提示する
2. **Given** 自動修正可能なエラーがある状態で、**When** ユーザーが修正を承認した時、**Then** Claude がファイルを修正する

---

### User Story 3 - Lint 設定のカスタマイズ (Priority: P3)

開発者として、プロジェクト固有の lint ルールを設定し、チーム全体で一貫したコードスタイルを維持したい。

**Why this priority**: 基本機能（P1, P2）が動作した上での拡張機能。

**Independent Test**: カスタム lint ルールを設定し、そのルールに従った lint が実行されることを確認する。

**Acceptance Scenarios**:

1. **Given** lint 設定ファイルが存在する状態で、**When** lint を実行した時、**Then** 設定ファイルのルールに従ってチェックが行われる
2. **Given** 設定ファイルがない状態で、**When** lint を実行した時、**Then** デフォルトのルールセットで lint が行われる

---

### Edge Cases

- lint ツールがインストールされていない場合 → エラーメッセージで通知し、インストール手順を案内
- lint 実行がタイムアウトした場合 → 適切なタイムアウト（10秒）を設け、超過時は警告のみで処理を継続
- 非常に大きなファイル（1000行超）の場合 → 大規模ファイルでも1秒以内に完了
- 構文エラーがある Python ファイルの場合 → 構文エラーを報告し、lint の他のチェックはスキップ

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは Claude Code の PostToolUse hook を使用して、Edit または Write ツール実行後に自動で処理を起動しなければならない
- **FR-002**: システムは編集されたファイルが `.py` 拡張子を持つ場合のみ lint を実行しなければならない
- **FR-003**: システムは lint 結果（エラー、警告、行番号、メッセージ）を Claude に返却しなければならない
- **FR-004**: システムは lint 結果をわかりやすい形式で出力しなければならない
- **FR-005**: システムは lint ツールが見つからない場合、エラーメッセージと対処方法を表示しなければならない
- **FR-006**: システムは lint 実行を10秒以内にタイムアウトしなければならない
- **FR-007**: システムは `make lint` コマンドを呼び出して lint を実行しなければならない

### Key Entities

- **Hook Configuration**: Claude Code の hooks 設定。PostToolUse イベントと matcher パターンを定義
- **Makefile Target**: `make lint` ターゲット。ruff を呼び出し、プロジェクト全体または指定ファイルの lint を実行
- **Lint Tool**: 実際の lint 処理を行うツール（ruff）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Python ファイル編集後、lint 結果が2秒以内に Claude に表示される
- **SC-002**: lint エラーの検出率は lint ツール単体実行時と同等（100%）である
- **SC-003**: Python 以外のファイル編集時に lint が誤って実行されることがない
- **SC-004**: lint 実行によるワークフロー中断が最小限に抑えられる（タイムアウト設定により）
- **SC-005**: 新規セットアップ時に5分以内で lint 環境が構築できる

## Assumptions

- **A-001**: lint ツールとして ruff を使用する（CLAUDE.md に記載あり、高速で Python 標準の lint・format を網羅）
- **A-002**: ruff は `pip install ruff` でインストール可能
- **A-003**: hook から `make lint` を呼び出す（Makefile で lint ロジックを一元管理）
- **A-004**: プロジェクトの Python コードは `src/` ディレクトリ配下に存在する
- **A-005**: lint 設定は `pyproject.toml` または `ruff.toml` で管理する

## Out of Scope

- CI/CD パイプラインでの lint 実行（本機能は開発時の即時フィードバックに特化）
- 他言語（JavaScript, TypeScript 等）の lint
- コードフォーマット（ruff format）の自動実行（lint チェックのみ）
- pre-commit hook との連携
