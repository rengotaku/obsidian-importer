# Feature Specification: E2Eテスト出力検証

**Feature Branch**: `046-e2e-output-validation`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "E2Eテストを正しく動作させる。インプット、アウトプットを定義して、アウトプットの出力内容の正しさを確認。LLMで出力内容がブレると思うので、正となる出力ファイルを作成したら90%似通っていたらOKのような形にする"

## Clarifications

### Session 2026-02-05

- Q: 検証対象はステージごとの出力か、最後のnodeの出力のみか → A: `format_markdown` の出力 Markdown (`markdown_notes`) のみを検証対象とする。中間ステージの出力は検証しない。
- Q: 最初のゴールデンファイルはどのように作成するのか → A: `make test-e2e-update-golden` 専用Makeターゲットで、E2Eパイプラインを実行し最終出力を `tests/fixtures/golden/` にコピーする。
- Q: E2Eテストの中間チェック（件数確認）はどうするか → A: 削除する。E2Eはパイプラインを一括実行し最終出力のみゴールデンファイルと比較する。中間ステージはユニットテストの責務とする。ただし、ユニットテストでは出力が空でないこと・成功状態であることを検証する。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - E2Eテストで最終出力の正しさを検証する (Priority: P1)

開発者がE2Eテスト (`make test-e2e`) を実行した際、パイプラインを `format_markdown` まで一括実行し、最終出力のMarkdownファイルをゴールデンファイルと比較して類似度ベースで検証する。中間ステージの個別チェックは行わない（ユニットテストの責務）。

**Why this priority**: 現状のE2Eテストは「ファイルが存在するか」のみの判定であり、出力内容が壊れていても検知できない。最終出力の検証はパイプラインの品質保証の根幹。

**Independent Test**: テストフィクスチャ (`claude_test.zip`) をパイプラインに通し、最終出力されたMarkdownファイルをゴールデンファイルと比較して類似度90%以上であることを確認する。

**Acceptance Scenarios**:

1. **Given** テストフィクスチャとゴールデンファイルが用意されている, **When** `make test-e2e` を実行する, **Then** パイプラインが一括実行され、最終Markdown出力がゴールデンファイルと比較され、類似度90%以上なら成功と判定される
2. **Given** パイプラインの出力が大きく崩れている（類似度90%未満）, **When** E2Eテストを実行する, **Then** テストが失敗し、どのファイルがどの程度乖離しているかが報告される
3. **Given** LLMの微妙な表現の揺れ（言い回しの違い、語順の変更）がある, **When** E2Eテストを実行する, **Then** 90%類似度の閾値内であればテスト成功と判定される

---

### User Story 2 - ゴールデンファイルの作成・更新 (Priority: P2)

開発者が `make test-e2e-update-golden` を実行してゴールデンファイル（正解データ）を初回生成または意図的に更新する。このコマンドはE2Eパイプラインを実行し、最終Markdown出力を `tests/fixtures/golden/` にコピーする。パイプラインの仕様変更やLLMモデル変更時に使用する。

**Why this priority**: ゴールデンファイルがなければ比較検証が成立しない。また、パイプライン変更時に更新手段がないと運用できない。

**Independent Test**: `make test-e2e-update-golden` を実行し、`tests/fixtures/golden/` にゴールデンファイルが作成されることを確認する。

**Acceptance Scenarios**:

1. **Given** ゴールデンファイルが存在しない, **When** `make test-e2e-update-golden` を実行する, **Then** パイプラインが実行され、最終Markdown出力が `tests/fixtures/golden/` にゴールデンファイルとして保存される
2. **Given** 既存のゴールデンファイルがある, **When** `make test-e2e-update-golden` を実行する, **Then** 既存ファイルが上書きされ、新しいゴールデンファイルが保存される

---

### User Story 3 - ユニットテストで中間ステージの基本的な正しさを保証する (Priority: P3)

既存のユニットテストを強化し、各ノードの出力が空でないこと・成功状態であることを検証する。E2Eテストから中間チェックを削除する代わりに、ユニットテストレベルで基本的な出力の妥当性を担保する。

**Why this priority**: E2Eから中間チェックを削除するため、ユニットテストで最低限の出力妥当性を保証する必要がある。

**Independent Test**: `make test` を実行し、各ノードのユニットテストが出力の非空・成功状態を検証することを確認する。

**Acceptance Scenarios**:

1. **Given** テストフィクスチャを入力とする, **When** 各ノードのユニットテストを実行する, **Then** 出力が空でないこと、必須キーが存在すること、成功状態であることが検証される

---

### Edge Cases

- LLMが極端に短い応答を返した場合（要約が数文字のみ）→ 類似度計算は可能だが、構造的な項目（frontmatter の title, tags 存在）の検証で検出
- LLMがタイムアウトした場合 → E2Eテスト全体が失敗として報告
- ゴールデンファイルが存在しない状態でテストを実行 → 明確なエラーメッセージで「先に `make test-e2e-update-golden` を実行してください」と案内
- テストフィクスチャのZIP内容が変更された場合 → ゴールデンファイルも再生成が必要
- 出力ファイル数がゴールデンファイル数と一致しない場合 → テスト失敗として報告

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: E2Eテストはパイプラインを `format_markdown` まで一括実行し、最終Markdown出力のみをゴールデンファイルと比較して検証しなければならない（中間ステージの個別チェックは削除する）
- **FR-002**: 最終Markdown出力とゴールデンファイルの類似度が90%以上であれば成功と判定しなければならない
- **FR-003**: 類似度の計算は、構造的類似度（frontmatterの必須キー存在、タグの重複率）と内容類似度（本文テキストの一致度）の組み合わせで行わなければならない
- **FR-004**: テスト失敗時は、どのファイルがどの程度乖離しているかを報告しなければならない
- **FR-005**: `make test-e2e-update-golden` コマンドでゴールデンファイルを生成・更新できなければならない。このコマンドはE2Eパイプラインを実行し、最終出力を `tests/fixtures/golden/` にコピーする
- **FR-006**: ゴールデンファイルはリポジトリにコミット可能な形式で `tests/fixtures/golden/` 配下に保存しなければならない
- **FR-007**: ゴールデンファイルが存在しない場合、テスト実行時に明確なエラーメッセージを表示しなければならない
- **FR-008**: 出力ファイル数とゴールデンファイル数が一致しない場合、テスト失敗として報告しなければならない
- **FR-009**: 各ノードのユニットテストは、出力が空でないこと・必須キーが存在すること・成功状態であることを検証しなければならない

### Key Entities

- **ゴールデンファイル**: `format_markdown` nodeの「正解」Markdown出力。`tests/fixtures/golden/` に保存され、リポジトリにコミットされる。`make test-e2e-update-golden` で生成・更新する
- **類似度スコア**: 2つのMarkdownファイル間の一致度を0〜100%で表す数値。構造的類似度と内容類似度の加重平均
- **テストフィクスチャ**: テスト用入力データ (`claude_test.zip`)。3件の会話を含む固定データ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: E2Eテスト実行時、最終Markdown出力がゴールデンファイルと90%以上の類似度であることを検証できる
- **SC-002**: パイプラインの出力が壊れた場合（frontmatter構造変更、キー欠落、本文の大幅な変化）、テストが確実に失敗する
- **SC-003**: テスト失敗時の報告から、問題箇所（ファイル名、乖離内容）を30秒以内に特定できる
- **SC-004**: `make test-e2e-update-golden` の1コマンドでゴールデンファイルの生成・更新が完了する
- **SC-005**: ユニットテストが各ノードの出力の非空・成功状態を検証している

## Assumptions

- テストフィクスチャ (`tests/fixtures/claude_test.zip`) は3件の会話を含み、変更されない前提
- Ollamaがローカルで起動していることがE2Eテストの前提条件（既存と同様）
- 類似度90%の閾値は初期値であり、運用を通じて調整可能とする
- ゴールデンファイルはLLMのモデル変更・プロンプト変更時に `make test-e2e-update-golden` で再生成が必要
- 検証対象は `format_markdown` nodeの出力（`markdown_notes`）のみ。中間ステージ（Extract、Transform途中）の出力はE2Eでは検証しない
- パイプラインは `parse_claude_zip` → `extract_knowledge` → `generate_metadata` → `format_markdown` の順に一括実行される
- 中間ステージの正しさはユニットテストで保証する（出力非空、必須キー存在、成功状態）
