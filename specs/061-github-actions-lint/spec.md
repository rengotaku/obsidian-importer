# Feature Specification: GitHub Actions Lint CI

**Feature Branch**: `061-github-actions-lint`
**Created**: 2026-02-23
**Status**: Draft
**Input**: Issue#35 - Add GitHub Actions for Lint (ruff + pylint)

## User Scenarios & Testing

### User Story 1 - PR 作成時の自動 lint チェック (Priority: P1)

開発者として、PR を作成または更新したとき、コードが自動的に lint チェックされることで、マージ前にコード品質の問題を検出できる。

**Why this priority**: コード品質の自動チェックは CI の最も基本的な機能であり、PR ワークフローに直接組み込まれることで開発者全員が恩恵を受ける。

**Independent Test**: PR を作成し、GitHub Actions の実行結果を確認することで、lint チェックが正常に動作することを検証できる。

**Acceptance Scenarios**:

1. **Given** lint エラーのないコードを含む PR が作成された, **When** GitHub Actions が実行される, **Then** lint チェックが成功し緑のステータスが表示される
2. **Given** lint エラーを含むコードの PR が作成された, **When** GitHub Actions が実行される, **Then** lint チェックが失敗し、エラー内容がログに表示される
3. **Given** 既存の PR が存在する, **When** PR に新しいコミットがプッシュされる, **Then** lint チェックが再実行される

---

### User Story 2 - main ブランチへの push 時の lint チェック (Priority: P2)

メンテナーとして、main ブランチにコードがマージされたとき、コード品質が維持されていることを確認できる。

**Why this priority**: main ブランチの品質維持は重要だが、PR 時点でチェック済みのため、セーフティネットとしての役割。

**Independent Test**: main ブランチに直接 push し、GitHub Actions の実行を確認することで検証できる。

**Acceptance Scenarios**:

1. **Given** main ブランチが存在する, **When** main ブランチにコードがプッシュされる, **Then** lint チェックが自動実行される

---

### User Story 3 - ローカルでの lint 実行 (Priority: P3)

開発者として、PR を作成する前にローカルで lint チェックを実行し、CI と同じ結果を得られる。

**Why this priority**: ローカル実行は CI の補助機能であり、フィードバックループを短縮するが、CI がなくても手動実行は可能。

**Independent Test**: `make lint` を実行し、ruff と pylint の両方が実行されることを確認する。

**Acceptance Scenarios**:

1. **Given** 開発環境がセットアップ済み, **When** `make lint` を実行する, **Then** ruff と pylint の両方がチェックを実行する
2. **Given** lint エラーが存在する, **When** `make lint` を実行する, **Then** 終了コードが非ゼロでエラー内容が表示される

---

### Edge Cases

- lint 対象のファイルが存在しない場合、チェックはスキップまたは成功として扱われる
- ローカル `make lint` 実行時、最初の linter が失敗した場合は後続の linter は実行せず即座に失敗となる（fail-fast）
- CI では ruff と pylint が独立して実行されるため、両方のエラーが同時に表示される
- 依存関係のインストールに失敗した場合、適切なエラーメッセージが表示される
- ローカルと CI でバージョンが異なる場合、pyproject.toml の固定バージョンに従うことで検出・防止される
- CI キャッシュミス時は通常のインストールにフォールバックし、処理は継続される

## Requirements

### Functional Requirements

- **FR-001**: CI は PR の作成・更新時に自動的にトリガーされなければならない
- **FR-002**: CI は main ブランチへの push 時に自動的にトリガーされなければならない
- **FR-003**: CI は Python 3.11 以上の環境でコードをチェックしなければならない
- **FR-004**: CI は ruff による lint チェックを実行しなければならない
- **FR-005**: CI は pylint による静的解析を実行しなければならない
- **FR-006**: CI の結果は PR のステータスとして表示されなければならない
- **FR-007**: CI が失敗した場合、エラーの詳細がログで確認できなければならない
- **FR-008**: ローカルの `make lint` コマンドで CI と同じチェックを実行できなければならない
- **FR-009**: pylint の設定は既存の pyproject.toml に追加されなければならない
- **FR-010**: pylint は開発依存関係として追加されなければならない
- **FR-011**: ruff と pylint のバージョンは pyproject.toml で固定されなければならない（ローカルと CI の結果一致を保証）
- **FR-012**: ローカルの `make lint` は fail-fast 方式で動作し、最初の linter 失敗で即座に終了しなければならない
- **FR-013**: Makefile は `ruff` と `pylint` の個別ターゲットを提供しなければならない
- **FR-014**: Makefile の `lint` ターゲットは `ruff` と `pylint` ターゲットを順次呼び出さなければならない
- **FR-015**: CI は `make ruff` と `make pylint` を個別に呼び出さなければならない（個別ステータス表示のため）
- **FR-016**: CI は pip 依存関係のキャッシュを利用し、インストール時間を短縮しなければならない

### Key Entities

- **Lint 結果**: 各 linter (ruff, pylint) のチェック結果、エラー有無、詳細メッセージ
- **CI ワークフロー**: トリガー条件、実行ステップ、環境設定を含む自動化プロセス
- **Makefile ターゲット**:
  - `ruff`: ruff チェックのみ実行
  - `pylint`: pylint チェックのみ実行
  - `lint`: ruff → pylint を順次実行（ローカル用）

## Success Criteria

### Measurable Outcomes

- **SC-001**: PR を作成すると 5 分以内に lint チェックが完了する
- **SC-002**: lint エラーがある場合、100% の確率で CI が失敗ステータスを返す
- **SC-003**: `make ruff` と `make pylint` でローカル実行した結果と CI の各ジョブ結果が一致する
- **SC-004**: 開発者は PR 画面で ruff と pylint の結果を個別に確認できる
- **SC-005**: lint エラーの修正に必要な情報がログから取得できる

## Clarifications

### Session 2026-02-24

- Q: ローカルと CI のツールバージョンをどのように一致させるか？ → A: pyproject.toml でバージョン固定
- Q: 一方の linter が失敗した場合、もう一方も実行するか？ → A: fail-fast（最初の失敗で停止）
- Q: CI と ローカルの実行差分をどう排除するか？ → A: CI は `make lint` を呼び出し、Makefile を単一の実行定義とする
- Q: Makefile ターゲット構成は？ → A: `ruff`, `pylint` を個別ターゲット化、`lint` は両方を呼び出す。CI は個別ターゲットを直接呼び出す
- Q: CI の依存関係インストールを高速化するか？ → A: pip キャッシュを利用する

## Assumptions

- ruff の設定は既存の pyproject.toml に定義済み
- GitHub Actions の利用が許可されたリポジトリである
- Python 3.11+ が CI 環境で利用可能である
- 依存関係のインストールに pip/pyproject.toml を使用する
