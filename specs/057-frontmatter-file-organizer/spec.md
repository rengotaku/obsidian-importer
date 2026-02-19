# Feature Specification: Frontmatter ファイル振り分けスクリプト

**Feature Branch**: `057-frontmatter-file-organizer`
**Created**: 2026-02-18
**Status**: Draft
**Input**: GitHub Issue #21 - frontmatterを読み込み分類してくれるスクリプトの作成

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 振り分けプレビュー確認 (Priority: P1)

ユーザーは、ファイルを実際に移動する前に、どのジャンルに何件のファイルが振り分けられるかをプレビューで確認したい。これにより、誤った振り分けを防ぎ、対象フォルダの存在確認も事前に行える。

**Why this priority**: 実際の移動前に確認できることで、取り返しのつかないファイル移動を防ぐ。安全性の観点から最優先。

**Independent Test**: プレビューモードのみで実行し、ジャンル別の件数と対象フォルダの存在状況が正しく表示されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 振り分け対象ファイルが存在する状態で、**When** プレビューモードで実行する、**Then** ジャンル別のファイル件数が一覧表示される
2. **Given** 振り分け対象ファイルが存在する状態で、**When** プレビューモードで実行する、**Then** 存在しない振り分け先フォルダに対して警告が表示される
3. **Given** 振り分け対象ファイルが0件の場合、**When** プレビューモードで実行する、**Then** 「対象ファイルがありません」と表示される

---

### User Story 2 - ファイル振り分け実行 (Priority: P2)

ユーザーは、frontmatter の genre と topic に基づいて、ファイルを適切なフォルダに振り分けたい。振り分け先は `{OUTPUT}/{genre}/{topic}/` 形式とする。

**Why this priority**: コア機能だが、P1のプレビュー確認を経てから実行するフローのため2番目の優先度。

**Independent Test**: 実際にファイルを移動し、正しいフォルダ構造に配置されることを確認できる。

**Acceptance Scenarios**:

1. **Given** genre=economy, topic=スマートフォン のファイルがある、**When** 振り分けを実行する、**Then** ファイルが `{OUTPUT}/経済/スマートフォン/` に移動される
2. **Given** 振り分け先フォルダが存在しない、**When** 振り分けを実行する、**Then** フォルダが自動作成されてファイルが移動される
3. **Given** 振り分けが完了した、**When** 処理結果を確認する、**Then** 移動成功件数と失敗件数が表示される

---

### User Story 3 - 入出力パス指定 (Priority: P3)

ユーザーは、デフォルトの入出力パスを使用するか、カスタムパスを指定して振り分けを実行したい。

**Why this priority**: 柔軟性を提供するが、デフォルト値があればMVPとして機能するため3番目。

**Independent Test**: カスタムパスを指定して実行し、指定したパスが正しく使用されることを確認できる。

**Acceptance Scenarios**:

1. **Given** パス指定なしで実行する、**When** スクリプトを実行する、**Then** デフォルトパス（INPUT=data/07_model_output/organized, OUTPUT=~/Documents/Obsidian/Vaults）が使用される
2. **Given** カスタム入力パスを指定する、**When** スクリプトを実行する、**Then** 指定した入力パスからファイルが読み込まれる
3. **Given** カスタム出力パスを指定する、**When** スクリプトを実行する、**Then** 指定した出力パスにファイルが振り分けられる

---

### Edge Cases

- genre または topic が frontmatter に存在しない場合 → `unclassified` フォルダに振り分け
- genre がマッピング表に存在しない場合 → `その他` フォルダに振り分け（警告表示）
- 同名ファイルが振り分け先に既に存在する場合 → スキップして警告を表示
- frontmatter が不正または読み取れない場合 → スキップしてエラーログに記録
- topic に含まれる特殊文字（/、\、:）がフォルダ名として使えない場合 → 安全な文字に置換
- `genre_mapping.yml` が存在しない場合 → エラー終了し、セットアップ手順を表示

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは Markdown ファイルの frontmatter から genre と topic を読み取れる必要がある
- **FR-011**: システムは英語の genre 値を日本語フォルダ名にマッピングする必要がある（マッピング表参照）
- **FR-012**: システムはマッピング表にない genre 値を `その他` フォルダに振り分け、警告を表示する必要がある
- **FR-013**: システムは `conf/base/genre_mapping.yml` からマッピング表を読み込む必要がある
- **FR-014**: システムは設定ファイルが存在しない場合、エラーメッセージとセットアップ手順を表示する必要がある
- **FR-015**: システムは `make organize-preview` でプレビューモード、`make organize` で実行モードを提供する必要がある
- **FR-002**: システムはプレビューモード（--dry-run）でジャンル別のファイル件数を表示できる必要がある
- **FR-003**: システムはプレビューモードで振り分け先フォルダの存在確認結果を表示できる必要がある
- **FR-004**: システムは `{OUTPUT}/{日本語genre}/{topic}/` の形式でファイルを振り分けできる必要がある
- **FR-005**: システムは振り分け先フォルダが存在しない場合、自動作成できる必要がある
- **FR-006**: システムは入力パスと出力パスをコマンドライン引数で指定できる必要がある
- **FR-007**: システムは genre/topic が未定義のファイルを `unclassified` フォルダに振り分ける必要がある
- **FR-008**: システムは同名ファイルが存在する場合、スキップして警告を表示する必要がある
- **FR-009**: システムは処理完了後、成功件数・スキップ件数・失敗件数のサマリーを表示する必要がある
- **FR-010**: システムは topic 内の特殊文字（/、\、:、*、?、"、<、>、|）を安全な文字に置換する必要がある

### Key Entities

- **振り分け対象ファイル**: Markdown ファイル。frontmatter に genre, topic, title 等のメタデータを含む
- **振り分け先フォルダ**: Obsidian Vault 内のジャンル別・トピック別フォルダ構造
- **振り分けルール**: frontmatter の genre → 第1階層フォルダ、topic → 第2階層フォルダ
- **Genre マッピング設定ファイル**: `conf/base/genre_mapping.yml`（gitignore 対象）
  - サンプルファイル `conf/base/genre_mapping.yml.sample` をコミット
  - ユーザーは sample をコピーして `genre_mapping.yml` を作成
  - デフォルトマッピング:

| frontmatter (英語) | フォルダ名 (日本語) |
|--------------------|---------------------|
| engineer           | エンジニア          |
| business           | ビジネス            |
| economy            | 経済                |
| daily              | 日常                |
| other              | その他              |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーはプレビューモードで5秒以内に振り分け計画を確認できる（1000ファイル以下の場合）
- **SC-002**: 振り分け処理は1ファイルあたり100ms以下で完了する
- **SC-003**: 同名ファイル衝突時のデータ損失が0件である
- **SC-004**: frontmatter 読み取り成功率が99%以上である（正しい形式のファイルに対して）
- **SC-005**: ユーザーは1コマンドでプレビュー確認から振り分け実行までのワークフローを完了できる

## Clarifications

### Session 2026-02-18

- Q: Genre フォルダ名の形式は？ → A: 英語 → 日本語マッピング（economy → 経済/）
- Q: マッピング表にない genre 値の扱いは？ → A: `その他` フォルダに振り分け（警告表示）
- Q: マッピング表の管理場所は？ → A: `conf/base/genre_mapping.yml`（gitignore 対象）、`genre_mapping.yml.sample` をコミット
- Q: Makefile ターゲット名は？ → A: `make organize-preview`（プレビュー）、`make organize`（実行）

## Assumptions

- 入力ファイルは全て Markdown 形式（.md 拡張子）
- frontmatter は YAML 形式で `---` で囲まれている
- genre の値は CLAUDE.md に定義された5種類（エンジニア、ビジネス、経済、日常、その他）に準拠
- topic の値は任意の文字列（ただしフォルダ名として安全な形式に変換）
- ユーザーは出力先ディレクトリへの書き込み権限を持っている

## Constraints

- Makefile 経由で実行可能であること
  - `make organize-preview`: プレビューモード（dry-run）
  - `make organize`: 振り分け実行
- Python 3.11+ で動作すること
- 外部ライブラリは PyYAML のみ使用可能（既存プロジェクト依存関係内）
