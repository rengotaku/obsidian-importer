# Feature Specification: データレイヤー分離（JSON/MD混在解消）

**Feature Branch**: `064-data-layer-separation`
**Created**: 2026-03-03
**Status**: Draft
**Input**: User description: "Issue#48"

## 概要

`data/07_model_output/` に混在している JSON 中間データと MD 最終出力を、Kedro のデータレイヤー設計に従って適切に分離する。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - パイプライン実行時のデータ整合性 (Priority: P1)

開発者として、パイプラインを実行したとき、中間データ（JSON）と最終出力（MD）が明確に分離されたディレクトリ構造で出力されることで、データの役割と処理段階を一目で把握できる。

**Why this priority**: データレイヤーの分離はこの機能の核心であり、他のすべての改善の基盤となる。これが達成されなければ、他のユーザーストーリーは意味をなさない。

**Independent Test**: `kedro run` を実行し、JSON ファイルが `05_model_input/` に、MD ファイルが `07_model_output/` にのみ出力されることを確認する。

**Acceptance Scenarios**:

1. **Given** パイプラインが実行される、**When** 正規化処理が完了する、**Then** JSON ファイルは `data/05_model_input/normalized/` に出力される
2. **Given** パイプラインが実行される、**When** 分類処理が完了する、**Then** JSON ファイルは `data/05_model_input/classified/` に出力される
3. **Given** パイプラインが実行される、**When** Markdown 生成が完了する、**Then** MD ファイルは `data/07_model_output/notes/` に出力される
4. **Given** `data/07_model_output/` ディレクトリ、**When** 内容を確認する、**Then** JSON ファイルは一切存在しない

---

### User Story 2 - 既存データの移行 (Priority: P2)

開発者として、既存の `07_model_output/` にある JSON ファイルを新しいレイヤー構造に移行できることで、データを失うことなくアップグレードできる。

**Why this priority**: 既存環境との互換性を確保し、スムーズな移行を可能にするために必要。P1 の新構造が決まってから対応可能。

**Independent Test**: 移行スクリプトを実行し、既存の JSON ファイルがすべて新しい場所に移動され、元の場所には残っていないことを確認する。

**Acceptance Scenarios**:

1. **Given** 旧構造に JSON ファイルが存在する、**When** 移行スクリプトを実行する、**Then** JSON ファイルは `data/05_model_input/` 配下の対応するディレクトリに移動される
2. **Given** 移行スクリプトを実行する、**When** 移行が完了する、**Then** 移行されたファイル数と移行先のサマリーが表示される
3. **Given** 一部のファイルがすでに移行先に存在する、**When** 移行スクリプトを実行する、**Then** 既存ファイルはスキップされ、スキップされたファイル数が報告される

---

### User Story 3 - ログ処理の簡素化 (Priority: P3)

開発者として、`iter_with_file_id` 関数が文字列（MD パス）のみを処理するようになることで、コードの複雑さが軽減され、保守性が向上する。

**Why this priority**: データレイヤー分離後に実施可能な改善。P1 と P2 が完了しないと、この簡素化は実現できない。

**Independent Test**: `iter_with_file_id` に文字列以外の入力を渡した場合にエラーが発生することを確認する。

**Acceptance Scenarios**:

1. **Given** `iter_with_file_id` 関数、**When** 文字列パスを入力する、**Then** 正常に処理され file_id が抽出される
2. **Given** `iter_with_file_id` 関数、**When** 辞書型を入力する、**Then** TypeError が発生する
3. **Given** リファクタリング後のコード、**When** 型チェックを行う、**Then** 辞書/文字列の分岐処理コードが削除されている

---

### Edge Cases

- 移行元ディレクトリに JSON ファイルが存在しない場合、スクリプトは正常終了し、移行対象がないことを報告する
- 移行先ディレクトリが存在しない場合、スクリプトが自動的に作成する
- 移行中にディスク容量が不足した場合、エラーメッセージを表示して処理を中断し、部分的に移行されたファイルのリストを出力する
- `07_model_output/` に残すべきでない JSON ファイルが検出された場合、警告を出力する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは JSON 中間データを `data/05_model_input/` ディレクトリに出力しなければならない
- **FR-002**: システムは MD 最終出力を `data/07_model_output/` ディレクトリに出力しなければならない
- **FR-003**: `conf/base/catalog.yml` は新しいディレクトリ構造を反映しなければならない
- **FR-004**: 移行スクリプトは既存の JSON ファイルを新しい場所に移動できなければならない
- **FR-005**: 移行スクリプトは移行結果のサマリーを出力しなければならない
- **FR-006**: `iter_with_file_id` 関数は文字列入力のみを受け付けるように簡素化されなければならない
- **FR-007**: 既存のテストは新しいディレクトリ構造に対応するよう更新されなければならない
- **FR-008**: パイプラインノードは新しい入出力パスを参照しなければならない

### Key Entities

- **05_model_input**: JSON 形式の中間データを格納するレイヤー。`normalized/`（正規化済み）、`classified/`（分類済み）、`cleaned/`（クリーニング済み）のサブディレクトリを持つ
- **07_model_output**: MD 形式の最終出力を格納するレイヤー。`notes/`（通常出力）、`review/`（レビュー対象）、`organized/`（ジャンル分類済み）のサブディレクトリを持つ
- **移行スクリプト**: 旧構造から新構造へのデータ移行を行うユーティリティ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: パイプライン実行後、`data/07_model_output/` 配下に JSON ファイルが 0 件である
- **SC-002**: パイプライン実行後、`data/05_model_input/` 配下に必要な JSON ファイルがすべて出力される
- **SC-003**: 既存のすべてのテストが新しいディレクトリ構造で合格する
- **SC-004**: `iter_with_file_id` 関数のコード行数が現状より減少する（辞書/文字列分岐の削除による）
- **SC-005**: 移行スクリプトが既存環境の JSON ファイルを 100% 正確に移行できる
- **SC-006**: パイプラインの処理時間が新構造導入前後で変化しない（±5% 以内）

## Assumptions

- 現在の `07_model_output/` にある JSON ファイルは、すべて中間データであり、最終出力ではない
- `05_model_input` は Kedro の慣例に従った適切なレイヤー番号である
- 移行は一度だけ実行され、継続的な同期は不要
- 既存の CI/CD パイプラインへの影響は最小限に抑えられる

## Dependencies

- Issue #63 (Ollama 例外リファクタリング) で `iter_with_file_id` の複雑さが顕在化したため、本機能と並行または先行して実施することが望ましい

## Scope Boundaries

### In Scope

- `catalog.yml` の更新
- 移行スクリプトの作成
- パイプラインノードの入出力パス更新
- `iter_with_file_id` の簡素化
- 関連テストの更新
- CLAUDE.md のディレクトリ構造説明の更新

### Out of Scope

- 新しいパイプラインノードの追加
- パイプラインロジックの変更（パスの変更のみ）
- データの内容やフォーマットの変更
- 他のデータレイヤー（01-04, 06）の変更
