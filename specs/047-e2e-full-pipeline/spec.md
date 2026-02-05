# Feature Specification: E2Eテスト フルパイプライン検証

**Feature Branch**: `047-e2e-full-pipeline`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "E2Eの改良。046-e2e-output-validationでの対応を踏まえて作業をすること"

## 背景

046-e2e-output-validation では `format_markdown` ノードまでの出力をゴールデンファイルと比較する E2E テストを構築した。しかし、実際のパイプラインはその後に Organize パイプライン（`classify_genre` → `normalize_frontmatter` → `clean_content` → `determine_vault_path` → `move_to_vault`）が続く。

現在のゴールデンファイルは `format_markdown` 出力であるため、以下が検証対象外となっている:

- ジャンル分類の正しさ
- frontmatter の正規化（不要フィールド除去、`normalized: true` 付与）
- コンテンツクリーニング（空行削減、末尾空白除去）
- Vault パス決定の正しさ
- 最終出力ファイルの frontmatter 構造（`summary`, `tags` の充実化など）

この改良では、パイプライン全体の最終出力を検証対象にすることで、E2E テストの信頼性を向上させる。

## User Scenarios & Testing

### User Story 1 - パイプライン最終出力のゴールデンファイル比較 (Priority: P1)

開発者として、パイプライン全体（Organize パイプラインを含む）の最終出力をゴールデンファイルと比較し、回帰を検出したい。

**Why this priority**: 046 の E2E テストは途中段階の出力しか検証していない。最終出力を検証することで、Organize パイプラインの回帰も検出できるようになる。これが本来の E2E テストの目的。

**Independent Test**: `make test-e2e` を実行し、最終出力（Organize 後）がゴールデンファイルと 80% 以上の類似度で一致することを確認できる。

**Acceptance Scenarios**:

1. **Given** ゴールデンファイルが `tests/fixtures/golden/` に存在する, **When** `make test-e2e` を実行する, **Then** パイプライン全体（`move_to_vault` まで）が実行され、最終出力がゴールデンファイルと比較される
2. **Given** パイプラインのロジックが変更されていない, **When** `make test-e2e` を実行する, **Then** 全ファイルの類似度が 80% 以上で成功判定される
3. **Given** Organize パイプラインのロジックが変更された, **When** `make test-e2e` を実行する, **Then** 類似度低下が検出され、開発者に差分が報告される

---

### User Story 2 - 最終出力のゴールデンファイル生成・更新 (Priority: P1)

開発者として、パイプライン全体の最終出力をゴールデンファイルとして生成・更新したい。

**Why this priority**: US1 の前提となるゴールデンファイルを生成する手段が必要。046 と同等の重要度。

**Independent Test**: `make test-e2e-update-golden` を実行し、Organize パイプライン後の最終出力が `tests/fixtures/golden/` に保存されることを確認できる。

**Acceptance Scenarios**:

1. **Given** Ollama が起動している, **When** `make test-e2e-update-golden` を実行する, **Then** パイプライン全体が実行され、最終出力（Organize 後）がゴールデンファイルとして保存される
2. **Given** 既存のゴールデンファイルがある, **When** `make test-e2e-update-golden` を実行する, **Then** 既存ファイルが新しい出力で上書きされる

---

### User Story 3 - ゴールデンファイルの frontmatter 完全検証 (Priority: P2)

開発者として、ゴールデンファイルの frontmatter が最終出力の構造（`summary`, 充実した `tags`, `file_id`, `normalized` 等）を正しく反映していることを確認したい。

**Why this priority**: frontmatter の構造変化は出力品質に直結するが、US1/US2 の仕組みが先に必要。

**Independent Test**: golden_comparator が Organize 後の frontmatter フィールド（`summary`, `tags` の充実度、`normalized`）を正しく比較できることを確認できる。

**Acceptance Scenarios**:

1. **Given** ゴールデンファイルに `summary` フィールドがある, **When** 実際の出力にも `summary` がある, **Then** frontmatter 類似度計算に `summary` が含まれる
2. **Given** ゴールデンファイルに充実した `tags` がある, **When** 実際の出力の `tags` が異なる, **Then** 類似度スコアが低下する
3. **Given** ゴールデンファイルに `normalized: true` がある, **When** 実際の出力に `normalized` がない, **Then** missing_keys として報告される

---

### Edge Cases

- パイプライン途中（Organize 前）で失敗した場合、最終出力ディレクトリが空になる → 明確なエラーメッセージ
- テスト環境で Vault ディレクトリへの書き込みが発生する → テスト用の一時ディレクトリに出力を制限
- LLM の非決定性による出力ブレ → 046 と同様、80% 閾値で許容
- Organize パイプラインが新しい frontmatter フィールドを追加した場合 → golden_comparator の必須キーリストを更新する必要がある

## Requirements

### Functional Requirements

- **FR-001**: `make test-e2e` はフルパイプラインの最終出力をゴールデンファイルと比較しなければならない（046 の `--to-nodes=format_markdown` 制限を撤廃）
- **FR-002**: `make test-e2e-update-golden` はフルパイプラインの最終出力をゴールデンファイルとして `tests/fixtures/golden/` に保存しなければならない
- **FR-003**: golden_comparator の frontmatter 比較は、Organize 後のフィールド（`summary`, `tags`, `file_id`, `normalized`）を正しく評価しなければならない
- **FR-004**: golden_comparator の必須キーリストは最終出力の frontmatter 構造に合わせて更新しなければならない（`title`, `created`, `tags`, `source_provider`, `file_id`, `normalized`, `summary`）
- **FR-005**: テスト実行時に Vault ディレクトリへの副作用（ファイル書き込み）が本番環境に影響しないようにしなければならない
- **FR-006**: ゴールデンファイル更新後、`make test-e2e` の自己比較（同一ファイル同士）で 100% の類似度が返らなければならない
- **FR-007**: 046 で構築した golden_comparator の既存テストが引き続き PASS しなければならない（後方互換性）

### Key Entities

- **ゴールデンファイル**: Organize パイプライン後の最終 Markdown 出力。frontmatter に `title`, `created`, `summary`, `tags`, `source_provider`, `file_id`, `normalized` を含む
- **類似度スコア**: 046 と同様の計算方式（frontmatter × 0.3 + body × 0.7）。frontmatter の評価対象フィールドが拡張される

## Success Criteria

### Measurable Outcomes

- **SC-001**: `make test-e2e` がフルパイプライン（Organize 含む）の最終出力を検証し、ゴールデンファイル自己比較で 100% の類似度を返す
- **SC-002**: ゴールデンファイルの frontmatter に `summary`, `tags`（非空）, `file_id`, `normalized: true` が含まれる
- **SC-003**: 046 で作成した golden_comparator のユニットテスト（37件以上）が全て PASS し続ける
- **SC-004**: `make test` で新規テスト含む全テストが PASS する（既知の RAG 関連エラーを除く）

## Assumptions

- 046 の golden_comparator.py および Makefile ターゲットを改修する形で進める（新規作成ではない）
- テスト環境（`--env=test`）の Kedro 設定で Vault 書き込み先を制御できる
- Organize パイプラインのテストフィクスチャ（`claude_test.zip`）は既存のものを使用する
- LLM の非決定性による出力ブレは 046 と同様、80% 閾値で許容する

## Scope

### In Scope

- Makefile `test-e2e` / `test-e2e-update-golden` ターゲットのフルパイプライン対応
- golden_comparator の frontmatter 必須キーリスト更新
- ゴールデンファイルの再生成（Organize 後の最終出力）
- テスト環境での Vault 書き込み制御

### Out of Scope

- 新しい比較アルゴリズムの導入（difflib.SequenceMatcher を継続使用）
- ジャンル分類精度の個別テスト（ユニットテストの責務）
- 複数プロバイダー（OpenAI, GitHub）の E2E テスト対応
- CI/CD パイプラインへの統合
