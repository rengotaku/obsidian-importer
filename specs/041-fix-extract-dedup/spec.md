# Feature Specification: 重複処理の解消

**Feature Branch**: `041-fix-extract-dedup`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "重複処理の解消"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ChatGPT エクスポートを正常にインポートできる (Priority: P1)

ChatGPT エクスポート ZIP ファイル（880MB、1,295 会話）をインポートした際、各会話が重複なく 1 回だけ処理され、正しい件数の Extract 出力が生成される。

**Why this priority**: 現在この処理が完全に壊れている。1,295 会話に対して 1,414,140 レコード（約 1,092 倍の重複）が出力されており、23GB のディスクを消費する。インポート機能が実質的に使用不能。

**Independent Test**: ChatGPT エクスポート ZIP をインポートし、Extract 出力の件数が ZIP 内の会話数と一致することを確認する。

**Acceptance Scenarios**:

1. **Given** 1,295 会話を含む ChatGPT エクスポート ZIP, **When** `make import INPUT=... PROVIDER=openai` を実行, **Then** Extract 出力のレコード数が会話数と等しい（MIN_MESSAGES フィルタで除外された会話を除く）
2. **Given** 同一の ZIP ファイル, **When** インポートを実行, **Then** pipeline_stages.jsonl に同一 conversation_uuid が 2 回以上出現しない
3. **Given** 1,295 会話を含む ZIP, **When** インポートを実行, **Then** extract/output/ のディスク使用量が入力 ZIP サイズの 10 倍以内に収まる

---

### User Story 2 - BaseExtractor の責務境界が明確である (Priority: P1)

BaseExtractor フレームワークにおいて、`_discover_raw_items()` と `steps` の責務が明確に分離されており、新しい Extractor を実装する際にどちらで何をすべきかが一意に決まる。

**Why this priority**: 現在のバグの根本原因はフレームワークの責務境界が曖昧であること。ChatGPTExtractor の `_discover_raw_items()` が ZIP 読み込み・パース・フォーマット変換のすべてを行い、同時に Steps も同じ処理を行っている。フレームワークレベルで責務を統一しなければ、今後の Extractor 追加時にも同じバグが発生する。

**Independent Test**: 全 Extractor（Claude、ChatGPT、GitHub）のコードを検査し、`_discover_raw_items()` と `steps` が重複した処理を行っていないことを確認する。

**Acceptance Scenarios**:

1. **Given** BaseExtractor を継承した任意の Extractor, **When** `discover_items()` の出力を `run()` に渡す, **Then** 各アイテムの処理が正確に 1 回だけ行われる
2. **Given** BaseExtractor のドキュメント（docstring）, **When** 新しい Extractor を実装する, **Then** `_discover_raw_items()` が何を返すべきか、`steps` が何を処理すべきかが明確に理解できる

---

### User Story 3 - 既存の全 Extractor が統一パターンに従う (Priority: P2)

BaseExtractor 系 3 種（Claude, ChatGPT, GitHub）が統一された設計パターンに従い、責務分担が一貫している。FileExtractor（BaseStage 直接継承）は回帰確認のみ。

現在の Extractor 一覧:

| Extractor | 継承元 | 用途 |
|-----------|--------|------|
| ClaudeExtractor | BaseExtractor | Claude エクスポート JSON/ZIP |
| ChatGPTExtractor | BaseExtractor | ChatGPT エクスポート ZIP |
| GitHubExtractor | BaseExtractor | GitHub Jekyll ブログ |
| FileExtractor | BaseStage（直接） | Markdown ファイル（organize Phase 用） |

**Why this priority**: 一貫性のない設計はメンテナンスコストを増大させる。統一パターンに揃えることで、将来の Extractor 追加（新プロバイダー対応）が安全にできる。FileExtractor は BaseExtractor を継承していないが、BaseStage の `run(steps)` を使用しているため同じ責務境界ルールが適用される。

**Independent Test**: 4 つの Extractor のコードレビューを行い、設計パターンの一貫性を確認する。

**Acceptance Scenarios**:

1. **Given** Claude エクスポート JSON, **When** `make import PROVIDER=claude` を実行, **Then** 既存の動作と同じ結果が得られる（回帰なし）
2. **Given** GitHub Jekyll リポジトリ URL, **When** `make import PROVIDER=github` を実行, **Then** 既存の動作と同じ結果が得られる（回帰なし）
3. **Given** ChatGPT エクスポート ZIP, **When** `make import PROVIDER=openai` を実行, **Then** 重複なく正常にインポートされる
4. **Given** Markdown ファイル群, **When** organize Phase で FileExtractor を使用, **Then** 既存の動作と同じ結果が得られる（回帰なし）

---

### User Story 4 - INPUT_TYPE と複数 INPUT に対応する (Priority: P2)

CLI の入力インターフェースを統一し、`--input-type`（デフォルト: `path`）で入力種別を明示的に指定できるようにする。また `--input` を複数回指定可能にする。

**Why this priority**: 現在 GitHub プロバイダーのみ URL 入力を特殊処理しており、プロバイダー依存の暗黙的な分岐がある。統一インターフェースにすることで、将来の入力種別追加が容易になる。

**Independent Test**: `--input-type url` で GitHub URL を指定し、`--input-type path` で ZIP ファイルを指定して、両方が正しく動作することを確認する。

**Acceptance Scenarios**:

1. **Given** `--input-type path`（デフォルト）, **When** `make import INPUT=dir PROVIDER=claude`, **Then** 既存と同じ動作（後方互換）
2. **Given** `--input-type url`, **When** `make import INPUT=https://... INPUT_TYPE=url PROVIDER=github`, **Then** GitHub インポートが正常動作
3. **Given** 複数 INPUT, **When** `make import INPUT=a.zip,b.zip PROVIDER=openai`, **Then** 両方の ZIP が 1 セッションで処理される
4. **Given** `--input-type` 省略で URL を指定, **When** `make import INPUT=https://... PROVIDER=github`, **Then** エラー（`--input-type url` の明示指定が必要）

---

### Edge Cases

- 空の conversations.json（0 会話）を含む ZIP の場合、正常に終了する（エラーにならない）
- mapping や current_node が欠損した会話が含まれている場合、その会話だけスキップされ、他の会話は正常に処理される
- 1 件のみの会話を含む ZIP ファイルで重複が発生しない
- チャンキング有効時（`discover_items(chunk=True)`）でも重複が発生しない
- `--input-type path` で存在しないパスを指定した場合、エラーメッセージを表示して終了コード 2
- `--input-type url` で不正な URL を指定した場合、エラーメッセージを表示して終了コード 1
- 複数 INPUT のうち 1 つが無効な場合、処理開始前に全 INPUT をバリデーションし、エラーを報告して処理を中止（fail-fast）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: BaseExtractor の `_discover_raw_items()` と `steps` の責務境界を明確に定義し、重複処理が構造的に発生しない設計にすること
- **FR-002**: ChatGPTExtractor において、`_discover_raw_items()` が yield したアイテムが `run(steps)` で再度展開されないこと
- **FR-003**: ClaudeExtractor の既存動作が変更されないこと（回帰テストの通過）
- **FR-004**: GitHubExtractor の既存動作が変更されないこと（回帰テストの通過）
- **FR-004b**: FileExtractor（BaseStage 直接継承）の既存動作が変更されないこと（回帰テストの通過）
- **FR-005**: `ImportPhase.run()` の `discover_items()` → `run()` 呼び出しパターンが全 Extractor で正しく機能すること
- **FR-006**: チャンキング機能（BaseExtractor._chunk_if_needed）が修正後も正常に動作すること
- **FR-007**: CLI が `--input-type`（`path` / `url`）で入力種別を明示的に指定できること（デフォルト: `path`）
- **FR-008**: `--input` を複数回指定可能にし、1 セッションで複数入力ソースを処理できること
- **FR-009**: `--input-type url` 未指定で URL を渡した場合、明確なエラーメッセージを出力すること

### Key Entities

- **BaseExtractor**: Extract ステージの基底クラス。Template Method パターンで `discover_items()` → `_discover_raw_items()` → `_chunk_if_needed()` を提供
- **Steps**: ステージ内の個別処理単位。入力 ProcessingItem を受け取り、変換して返す。1:1 または 1:N の展開が可能
- **ProcessingItem**: パイプラインを流れるデータ単位。`item_id`, `content`, `metadata`, `source_path` を持つ
- **discover_items() / run() の境界**: discover が「何を処理するか」を決定し、run(steps) が「どう処理するか」を実行する

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ChatGPT エクスポート（1,295 会話）のインポートで、Extract 出力レコード数が会話数と等しいこと（MIN_MESSAGES フィルタ除外分を除く）
- **SC-002**: 全 Extractor（Claude、ChatGPT、GitHub、File）の既存ユニットテストが 100% 通過すること
- **SC-003**: `_discover_raw_items()` と `steps` で同一処理（ZIP 読み込み、パース、フォーマット変換）が重複して実行されないこと
- **SC-004**: Extract ステージの出力に同一 `conversation_uuid` が複数回出現しないこと
- **SC-005**: `make import INPUT=dir PROVIDER=claude` が `--input-type path`（デフォルト）で動作すること
- **SC-006**: 複数 INPUT 指定時、全入力ソースのアイテムが 1 セッションで処理されること
