# Feature Specification: E2Eテスト フルパイプライン検証

**Feature Branch**: `047-e2e-full-pipeline`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "E2Eの改良。046-e2e-output-validationでの対応を踏まえて作業をすること"

## Clarifications

### Session 2026-02-05

- Q: E2E テストでの Vault 書き込み範囲は？ → A: パイプラインを変更し、ファイルシステムへの Vault 書き込みを廃止。振り分け情報（genre, vault_path）は frontmatter に記載する方式に変更。

## 背景

046-e2e-output-validation では `format_markdown` ノードまでの出力をゴールデンファイルと比較する E2E テストを構築した。しかし、実際のパイプラインはその後に Organize パイプライン（`classify_genre` → `normalize_frontmatter` → `clean_content` → `determine_vault_path` → `move_to_vault`）が続く。

現在のゴールデンファイルは `format_markdown` 出力であるため、以下が検証対象外となっている:

- ジャンル分類の正しさ
- frontmatter の正規化（不要フィールド除去、`normalized: true` 付与）
- コンテンツクリーニング（空行削減、末尾空白除去）
- Vault パス決定の正しさ
- 最終出力ファイルの frontmatter 構造（`summary`, `tags` の充実化など）

### 設計変更: Vault 書き込みの廃止

現行の `move_to_vault` ノードはファイルシステムに直接書き込む副作用を持つ。この設計には以下の問題がある:

1. **テスト環境での副作用制御が複雑** - テスト時に本番 Vault を汚染しないよう設定が必要
2. **冪等性の担保が困難** - 同じファイルを再実行すると上書きが発生
3. **E2E 検証の複雑化** - ファイルシステムの状態を比較対象にする必要がある

本 feature では、パイプラインを以下のように変更する:

- `move_to_vault` ノードを **ファイル書き込みなし** に変更（または廃止）
- 振り分け情報（`genre`, `vault_path`）を **frontmatter に埋め込む**
- 最終出力は `data/07_model_output/notes/*.md` に統一（Vault ディレクトリへの分散配置なし）
- Vault への実際の配置は **別プロセス（手動または別コマンド）** で行う

## User Scenarios & Testing

### User Story 1 - パイプライン最終出力のゴールデンファイル比較 (Priority: P1)

開発者として、パイプライン全体（Organize パイプラインを含む）の最終出力をゴールデンファイルと比較し、回帰を検出したい。

**Why this priority**: 046 の E2E テストは途中段階の出力しか検証していない。最終出力を検証することで、Organize パイプラインの回帰も検出できるようになる。これが本来の E2E テストの目的。

**Independent Test**: `make test-e2e` を実行し、最終出力（Organize 後、frontmatter に genre/vault_path 含む）がゴールデンファイルと 80% 以上の類似度で一致することを確認できる。

**Acceptance Scenarios**:

1. **Given** ゴールデンファイルが `tests/fixtures/golden/` に存在する, **When** `make test-e2e` を実行する, **Then** パイプライン全体が実行され、最終 Markdown 出力がゴールデンファイルと比較される
2. **Given** パイプラインのロジックが変更されていない, **When** `make test-e2e` を実行する, **Then** 全ファイルの類似度が 80% 以上で成功判定される
3. **Given** Organize パイプラインのロジックが変更された, **When** `make test-e2e` を実行する, **Then** 類似度低下が検出され、開発者に差分が報告される

---

### User Story 2 - 最終出力のゴールデンファイル生成・更新 (Priority: P1)

開発者として、パイプライン全体の最終出力をゴールデンファイルとして生成・更新したい。

**Why this priority**: US1 の前提となるゴールデンファイルを生成する手段が必要。046 と同等の重要度。

**Independent Test**: `make test-e2e-update-golden` を実行し、Organize パイプライン後の最終出力が `tests/fixtures/golden/` に保存されることを確認できる。

**Acceptance Scenarios**:

1. **Given** Ollama が起動している, **When** `make test-e2e-update-golden` を実行する, **Then** パイプライン全体が実行され、最終出力（frontmatter に genre/vault_path 含む）がゴールデンファイルとして保存される
2. **Given** 既存のゴールデンファイルがある, **When** `make test-e2e-update-golden` を実行する, **Then** 既存ファイルが新しい出力で上書きされる

---

### User Story 3 - ゴールデンファイルの frontmatter 完全検証 (Priority: P2)

開発者として、ゴールデンファイルの frontmatter が最終出力の構造（`genre`, `vault_path`, `summary`, 充実した `tags`, `file_id`, `normalized` 等）を正しく反映していることを確認したい。

**Why this priority**: frontmatter の構造変化は出力品質に直結するが、US1/US2 の仕組みが先に必要。

**Independent Test**: golden_comparator が Organize 後の frontmatter フィールド（`genre`, `vault_path`, `summary`, `tags` の充実度、`normalized`）を正しく比較できることを確認できる。

**Acceptance Scenarios**:

1. **Given** ゴールデンファイルに `genre` と `vault_path` フィールドがある, **When** 実際の出力にも同じ値がある, **Then** frontmatter 類似度が高く計算される
2. **Given** ゴールデンファイルに `summary` フィールドがある, **When** 実際の出力にも `summary` がある, **Then** frontmatter 類似度計算に `summary` が含まれる
3. **Given** ゴールデンファイルに充実した `tags` がある, **When** 実際の出力の `tags` が異なる, **Then** 類似度スコアが低下する

---

### User Story 4 - パイプライン変更: Vault 書き込み廃止 (Priority: P1)

開発者として、Organize パイプラインがファイルシステムに直接書き込まないように変更したい。振り分け情報は frontmatter に埋め込む。

**Why this priority**: E2E テストの前提となるパイプライン変更。テスト環境の副作用制御が不要になり、シンプルな設計になる。

**Independent Test**: `kedro run` を実行し、`Vaults/` ディレクトリにファイルが作成されないこと、かつ `data/07_model_output/notes/*.md` の frontmatter に `genre` と `vault_path` が含まれることを確認できる。

**Acceptance Scenarios**:

1. **Given** パイプラインを実行する, **When** Organize ステージが完了する, **Then** `Vaults/` ディレクトリにファイルが作成されない
2. **Given** パイプラインを実行する, **When** 最終 Markdown が出力される, **Then** frontmatter に `genre`（例: `engineer`, `business`）と `vault_path`（例: `Vaults/エンジニア/`）が含まれる
3. **Given** 既存のユニットテストがある, **When** パイプライン変更後に `make test` を実行する, **Then** Organize パイプラインの既存テストが PASS する（後方互換性）

---

### Edge Cases

- パイプライン途中（Organize 前）で失敗した場合、最終出力ディレクトリが空になる → 明確なエラーメッセージ
- LLM の非決定性による出力ブレ → 046 と同様、80% 閾値で許容
- Organize パイプラインが新しい frontmatter フィールドを追加した場合 → golden_comparator の必須キーリストを更新する必要がある
- `genre` が `other` に分類された場合 → `vault_path` は `Vaults/その他/` となる

## Requirements

### Functional Requirements

#### E2E テスト関連

- **FR-001**: `make test-e2e` はフルパイプラインの最終出力をゴールデンファイルと比較しなければならない（046 の `--to-nodes=format_markdown` 制限を撤廃）
- **FR-002**: `make test-e2e-update-golden` はフルパイプラインの最終出力をゴールデンファイルとして `tests/fixtures/golden/` に保存しなければならない
- **FR-003**: golden_comparator の frontmatter 比較は、Organize 後のフィールド（`genre`, `vault_path`, `summary`, `tags`, `file_id`, `normalized`）を正しく評価しなければならない
- **FR-004**: golden_comparator の必須キーリストは最終出力の frontmatter 構造に合わせて更新しなければならない（`title`, `created`, `tags`, `source_provider`, `file_id`, `normalized`, `summary`, `genre`, `vault_path`）
- **FR-005**: ゴールデンファイル更新後、`make test-e2e` の自己比較（同一ファイル同士）で 100% の類似度が返らなければならない
- **FR-006**: 046 で構築した golden_comparator の既存テストが引き続き PASS しなければならない（後方互換性）

#### パイプライン変更関連

- **FR-007**: Organize パイプラインはファイルシステム（`Vaults/` ディレクトリ）への書き込みを行ってはならない
- **FR-008**: 最終 Markdown 出力の frontmatter に `genre` フィールド（`engineer`, `business`, `economy`, `daily`, `other` のいずれか）を含めなければならない
- **FR-009**: 最終 Markdown 出力の frontmatter に `vault_path` フィールド（例: `Vaults/エンジニア/`）を含めなければならない
- **FR-010**: パイプライン変更後も Organize パイプラインの既存ユニットテストが PASS しなければならない

### Key Entities

- **ゴールデンファイル**: Organize パイプライン後の最終 Markdown 出力。frontmatter に `title`, `created`, `summary`, `tags`, `source_provider`, `file_id`, `normalized`, `genre`, `vault_path` を含む
- **類似度スコア**: 046 と同様の計算方式（frontmatter × 0.3 + body × 0.7）。frontmatter の評価対象フィールドが拡張される

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make test-e2e` がフルパイプライン（Organize 含む）の最終出力を検証し、ゴールデンファイル自己比較で 100% の類似度を返す
- **SC-002**: ゴールデンファイルの frontmatter に `summary`, `tags`（非空）, `file_id`, `normalized: true`, `genre`, `vault_path` が含まれる
- **SC-003**: 046 で作成した golden_comparator のユニットテスト（37件以上）が全て PASS し続ける
- **SC-004**: `make test` で新規テスト含む全テストが PASS する（既知の RAG 関連エラーを除く）
- **SC-005**: `kedro run` 実行後、`Vaults/` ディレクトリにファイルが作成されない

## Assumptions

- 046 の golden_comparator.py および Makefile ターゲットを改修する形で進める（新規作成ではない）
- Organize パイプラインのテストフィクスチャ（`claude_test.zip`）は既存のものを使用する
- LLM の非決定性による出力ブレは 046 と同様、80% 閾値で許容する
- Vault への実際のファイル配置は本 feature のスコープ外（別コマンドまたは手動）

## Scope

### In Scope

- Makefile `test-e2e` / `test-e2e-update-golden` ターゲットのフルパイプライン対応
- golden_comparator の frontmatter 必須キーリスト更新（`genre`, `vault_path` 追加）
- ゴールデンファイルの再生成（Organize 後の最終出力）
- **Organize パイプラインの変更**: `move_to_vault` のファイル書き込み廃止
- **frontmatter への振り分け情報埋め込み**: `genre`, `vault_path` フィールド追加

### Out of Scope

- 新しい比較アルゴリズムの導入（difflib.SequenceMatcher を継続使用）
- ジャンル分類精度の個別テスト（ユニットテストの責務）
- 複数プロバイダー（OpenAI, GitHub）の E2E テスト対応
- CI/CD パイプラインへの統合
- Vault への実際のファイル配置コマンド（別 feature で対応）
