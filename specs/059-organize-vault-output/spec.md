# Feature Specification: Organize パイプラインの Obsidian Vault 直接出力対応

**Feature Branch**: `059-organize-vault-output`
**Created**: 2026-02-20
**Status**: Draft
**Input**: Issue#24 - Organize パイプラインの Obsidian Vault 直接出力対応

## Clarifications

### Session 2026-02-20

- Q: `kedro run` をパイプライン指定なしで実行した場合、`organize_to_vault` は実行されるか？ → A: 実行されない（独立パイプラインとして明示的に `--pipeline=organize_to_vault` の指定が必要）
- Q: どのフォルダを Vault 出力の対象とするか？ → A: `organized/` のみ（`organized_review/` は対象外）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vault 出力先の事前確認 (Priority: P1)

ユーザーは、ファイルを実際に移動する前に、各ファイルがどの Vault のどのフォルダに出力されるかを事前確認したい。既存ファイルとの競合も事前に把握して、データ損失を防ぎたい。

**Why this priority**: ファイル移動は不可逆な操作であり、事前確認なしに実行すると意図しない上書きやデータ損失が発生する可能性がある。Preview 機能は安全な運用の基盤となる。

**Independent Test**: `kedro run --pipeline=organize_preview` を実行し、ファイルの出力先一覧と競合情報が表示されることを確認。実際のファイル移動は発生しない。

**Acceptance Scenarios**:

1. **Given** organized フォルダに 10 件のファイルがある, **When** organize_preview パイプラインを実行する, **Then** 各ファイルの出力先 Vault パスが一覧表示される
2. **Given** 出力先に同名ファイルが存在する, **When** organize_preview を実行する, **Then** 競合ファイルが警告として表示される
3. **Given** organized フォルダにファイルがある, **When** organize_preview を実行する, **Then** ジャンル別の件数サマリーが表示される

---

### User Story 2 - Vault への自動ファイル出力 (Priority: P2)

ユーザーは、ジャンル分類されたファイルを適切な Obsidian Vault に自動的にコピーしたい。手動でファイルを移動する手間を省き、ナレッジベースを効率的に構築したい。

**Why this priority**: ファイルの自動出力はこの機能の中核であり、Preview で確認後に実行する主要な操作。ただし Preview なしでは安全に運用できないため P2 とする。

**Independent Test**: `kedro run --pipeline=organize_to_vault` を実行し、ファイルが正しい Vault にコピーされることを確認。

**Acceptance Scenarios**:

1. **Given** genre が "ai" のファイルがある, **When** organize_to_vault を実行する, **Then** ファイルは「エンジニア」Vault にコピーされる
2. **Given** topic が "Python" のファイルがある, **When** organize_to_vault を実行する, **Then** ファイルは Vault 内の「Python」サブフォルダに配置される
3. **Given** topic が空のファイルがある, **When** organize_to_vault を実行する, **Then** ファイルは Vault 直下に配置される

---

### User Story 3 - 競合ファイルのスキップ (Priority: P3)

ユーザーは、既存のファイルを誤って上書きしないよう、競合がある場合は自動的にスキップしてほしい。

**Why this priority**: デフォルトの安全な動作として重要だが、P1/P2 が動作することが前提となる。

**Independent Test**: 既存ファイルがある状態で `--skip` オプション付きで実行し、既存ファイルが維持されることを確認。

**Acceptance Scenarios**:

1. **Given** 出力先に同名ファイルが存在する, **When** `--skip` オプションで実行する, **Then** 既存ファイルは維持され新しいファイルはコピーされない
2. **Given** 3 件中 1 件が競合する, **When** `--skip` オプションで実行する, **Then** 2 件がコピーされ 1 件がスキップされた旨のログが出力される

---

### User Story 4 - 競合ファイルの上書き (Priority: P4)

ユーザーは、意図的に既存ファイルを最新版で上書きしたい場合がある。

**Why this priority**: 明示的に指定された場合のみ動作する追加オプション。

**Independent Test**: 既存ファイルがある状態で `--overwrite` オプション付きで実行し、ファイルが更新されることを確認。

**Acceptance Scenarios**:

1. **Given** 出力先に同名ファイルが存在する, **When** `--overwrite` オプションで実行する, **Then** 既存ファイルが新しい内容で上書きされる

---

### User Story 5 - 競合ファイルの別名保存 (Priority: P5)

ユーザーは、既存ファイルも新しいファイルも両方保持したい場合がある。

**Why this priority**: 特殊なユースケース向けの追加オプション。

**Independent Test**: 既存ファイルがある状態で `--increment` オプション付きで実行し、別名でファイルが作成されることを確認。

**Acceptance Scenarios**:

1. **Given** `file.md` が出力先に存在する, **When** `--increment` オプションで実行する, **Then** `file_1.md` として新しいファイルが作成される
2. **Given** `file.md` と `file_1.md` が存在する, **When** `--increment` オプションで実行する, **Then** `file_2.md` として新しいファイルが作成される

---

### Edge Cases

- topic に特殊文字（スラッシュ、バックスラッシュ等）が含まれる場合は、安全なフォルダ名に正規化する
- Vault ベースパスが存在しない場合はエラーを出力して処理を中断する
- ファイルの genre が Vault マッピングに存在しない場合は「その他」Vault に出力する
- 権限エラー（書き込み不可）の場合は、該当ファイルをスキップしてログに記録する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは genre に基づいて出力先 Vault を決定できること
- **FR-002**: システムは topic をサブフォルダとして使用し、genre はフォルダを作成しないこと
- **FR-003**: システムは Preview モードで実際のファイル移動を行わず、出力先一覧と競合情報を表示できること
- **FR-004**: システムは既存ファイルとの競合を検出し、指定された方法（skip/overwrite/increment）で処理できること
- **FR-005**: システムはジャンル別の件数サマリーを表示できること
- **FR-006**: システムは設定ファイルから Vault ベースパスと genre-Vault マッピングを読み込めること
- **FR-007**: システムは競合処理オプションをコマンドラインパラメータで受け取れること
- **FR-008**: システムは処理結果（成功/スキップ/エラー件数）をログに出力すること
- **FR-009**: `organize_preview` と `organize_to_vault` は独立パイプラインとして登録し、`__default__` には含めないこと（明示的な `--pipeline` 指定を必須とする）

### Key Entities

- **OrganizedFile**: ジャンル分類済みのファイル。genre、topic、ファイルパスを持つ
- **VaultDestination**: 出力先情報。Vault 名、サブフォルダパス、最終ファイルパスを持つ
- **ConflictInfo**: 競合情報。ソースファイル、既存ファイル、競合タイプを持つ
- **VaultMapping**: genre から Vault 名へのマッピング設定

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーは Preview モードで 100 件のファイルの出力先を 10 秒以内に確認できる
- **SC-002**: ファイルは正しい Vault に 100% の精度で振り分けられる（genre-Vault マッピングに基づく）
- **SC-003**: 競合検出は 100% の精度で機能し、意図しない上書きが発生しない
- **SC-004**: ユーザーは手動操作なしで organized フォルダから Vault への移動を完了できる
- **SC-005**: 処理エラーが発生した場合、ユーザーは原因と対処方法を理解できるログが出力される

## Assumptions

- Vault ベースパスは `/home/takuya/Documents/Obsidian/Vaults` とする（設定で変更可能）
- デフォルトの競合処理は `skip` とする
- organized フォルダ内のファイルは frontmatter に genre と topic が含まれている
- Vault は事前に作成済みであり、このパイプラインでは Vault 自体の作成は行わない
- ソースフォルダは `data/07_model_output/organized/` のみ（`organized_review/` は品質確認が必要なため対象外）

## Scope Boundaries

### In Scope

- organized フォルダから Vault へのファイルコピー
- Preview モードでの出力先確認と競合検出
- 3 種類の競合処理オプション（skip/overwrite/increment）
- ジャンル別件数サマリーの表示

### Out of Scope

- Vault の自動作成
- ファイルの削除（コピー元のファイルは残る）
- 双方向同期
- Vault 内の既存ファイルの再分類
