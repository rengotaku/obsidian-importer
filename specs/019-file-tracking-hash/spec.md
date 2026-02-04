# Feature Specification: ファイル追跡ハッシュID

**Feature Branch**: `019-file-tracking-hash`
**Created**: 2026-01-17
**Status**: Draft
**Input**: User description: "インポートからorganizeのファイルを追跡したい。現状だとファイル名で終えるかもしれないが途中で名前変更などが発生していまいちわかりにくい。初期のファイルからhash値を求めて以降はIDとして利用して後続の処理で行うようにしたい。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ファイル追跡IDの自動生成 (Priority: P1)

ユーザーがファイルをインポートまたは処理開始した際、システムはファイルごとに一意のハッシュIDを自動生成し、セッションログに記録する。これにより、ファイル名が変更されても元のファイルを追跡できる。

**Why this priority**: ファイル追跡の基盤機能であり、ログ連携機能がこのID生成に依存するため最優先。

**Independent Test**: 任意のファイルを処理し、生成されたIDがセッションログに記録されていることを確認。

**Acceptance Scenarios**:

1. **Given** 新規ファイルが `@index/` に追加された, **When** 処理を開始する, **Then** ファイルごとに一意のハッシュIDが生成され、セッションログに記録される
2. **Given** 同一コンテンツの複数ファイル, **When** 処理を実行する, **Then** 各ファイルに異なるハッシュIDが付与される（ファイルごとに一意）

---

### User Story 2 - 処理履歴のID連携 (Priority: P2)

セッションログ（`processed.json`, `errors.json`）内の各エントリにハッシュIDを含め、ファイル名に依存せずに処理履歴を参照できるようにする。

**Why this priority**: ログの利便性向上だが、P1のID生成が前提となるため優先度2。

**Independent Test**: 処理実行後、`processed.json`内のエントリにハッシュIDが含まれていることを確認。

**Acceptance Scenarios**:

1. **Given** ファイル処理が完了した, **When** `processed.json`を確認する, **Then** 各エントリに`file_id`フィールドが含まれる
2. **Given** ファイル名が変更された後, **When** ハッシュIDで履歴を検索する, **Then** 変更前のファイル名での処理履歴も見つかる

---

### Edge Cases

- 空ファイルの場合：空文字列 + 初回パスのハッシュを使用（ファイルごとに一意）
- 同一コンテンツの複数ファイル：初回パスが異なるため異なるIDが生成される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、ファイル処理開始時にファイルごとに一意のハッシュIDを生成しなければならない
- **FR-002**: ファイルIDは短縮形式（8-12文字）で表示し、ログの可読性を確保しなければならない
- **FR-003**: `processed.json`および`errors.json`の各エントリに`file_id`フィールドを含めなければならない

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: セッションログ内で任意のファイルIDを検索し、該当ファイルの処理履歴を特定できる
- **SC-002**: ファイルID生成による処理時間増加は1ファイルあたり10ms以下

## Assumptions

- ハッシュはコンテンツ + 初回パスから生成し、ファイルごとに一意性を保証
- 既存の`ProcessingResult`型に`file_id`フィールドを追加する形で拡張
