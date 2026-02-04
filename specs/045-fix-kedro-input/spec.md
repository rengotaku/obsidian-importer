# Feature Specification: Kedro 入力フロー修正

**Feature Branch**: `045-fix-kedro-input`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "kedro-runを動くようにする。Inputの再設計が必要。"

## Clarifications

### Session 2026-02-04

- Q: Claude/OpenAI の入力形式は？ → A: 両プロバイダーとも ZIP ファイルを入力とする（統一）
- Q: Claude ZIP 内のファイル構造は？ → A: ZIP 直下に `conversations.json` がある前提（OpenAI と同じ構造）
- Q: GitHub プロバイダーの入力方式は？ → A: URL パラメータ指定のまま維持
- Q: ZIP ファイルの配置パスは？ → A: `data/01_raw/{provider}/` に配置された全 ZIP を処理（複数ファイル対応）。会話アイテム単位で冪等 Resume が機能する
- Q: `import.provider` パラメータは？ → A: 残す。パイプラインは dispatch 型設計とし、`import.provider` で振り分ける
- Q: 問題の範囲は？ → A: 入力層（カタログ定義 ↔ ノードシグネチャ）のみ。統合テストは MemoryDataset で直接データ注入しているためパスするが、実環境の catalog.yml 経由では型不一致で動作しない
- Q: テスト用 ZIP フィクスチャの作成方針は？ → A: 実データから数件抽出し `tests/fixtures/` に静的配置。`claude_test.zip`（3会話）、`openai_test.zip`（3会話）を作成済み

## User Scenarios & Testing *(mandatory)*

### User Story 1 - dispatch 型パイプラインによるインポート実行 (Priority: P1)

ユーザーは `import.provider` パラメータ（デフォルト: `claude`）を指定して `kedro run` を実行する。システムは provider に応じた Extract パイプラインに dispatch し、Transform → Organize と一貫して処理を実行する。

**Why this priority**: 全プロバイダー共通のエントリポイントであり、dispatch 型設計の根幹。これが動かなければ個別プロバイダーも動かない。

**Independent Test**: `kedro run --params='{"import.provider": "claude"}'` を実行してパイプラインが正しく dispatch されることを確認する。

**Acceptance Scenarios**:

1. **Given** `import.provider=claude` が設定されている状態, **When** `kedro run` を実行, **Then** Claude Extract → Transform → Organize パイプラインが実行される
2. **Given** `import.provider=openai` が設定されている状態, **When** `kedro run` を実行, **Then** OpenAI Extract → Transform → Organize パイプラインが実行される
3. **Given** `import.provider=github` が設定されている状態, **When** `kedro run` を実行, **Then** GitHub Extract → Transform → Organize パイプラインが実行される
4. **Given** 無効な provider が指定されている状態, **When** `kedro run` を実行, **Then** わかりやすいエラーメッセージが表示される

---

### User Story 2 - Claude/OpenAI ZIP ファイルからのインポート (Priority: P1)

ユーザーはエクスポート ZIP ファイルを `data/01_raw/{provider}/` に配置し、`kedro run` を実行する。ZIP 内の `conversations.json` がパースされ、Obsidian Markdown ノートが Vault に配置される。

**Why this priority**: Claude と OpenAI は最も頻繁に使用されるプロバイダー。ZIP 入力の統一により、両プロバイダーのカタログ定義とノードシグネチャの整合性を確保する。

**Independent Test**: テスト用 ZIP を `data/01_raw/claude/` に配置し、`kedro run` を実行して Markdown が生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** Claude エクスポート ZIP が `data/01_raw/claude/` に配置されている状態, **When** `kedro run` を実行, **Then** ZIP 内の `conversations.json` がパースされ、Obsidian Markdown が生成される
2. **Given** ChatGPT エクスポート ZIP が `data/01_raw/openai/` に配置されている状態, **When** `kedro run --params='{"import.provider": "openai"}'` を実行, **Then** ZIP 内の `conversations.json` がパースされ、Obsidian Markdown が生成される
3. **Given** 複数の ZIP が `data/01_raw/claude/` に配置されている状態, **When** `kedro run` を実行, **Then** 全 ZIP が処理される
4. **Given** 前回の実行で一部が完了済みの状態, **When** 同じコマンドを再実行, **Then** 完了済みアイテムはスキップされ、未処理分のみ実行される（冪等 Resume）
5. **Given** 入力ディレクトリにファイルが存在しない状態, **When** `kedro run` を実行, **Then** わかりやすいエラーメッセージが表示される
6. **Given** 破損した ZIP ファイルが配置されている状態, **When** パイプラインを実行, **Then** エラーメッセージが出力され、他のファイルの処理は継続される

---

### User Story 3 - GitHub Jekyll ブログのインポート (Priority: P3)

ユーザーは `import.provider=github` と GitHub リポジトリ URL をパラメータで指定し、`kedro run` を実行する。Jekyll ブログ記事が Obsidian ノートとして取り込まれる。

**Why this priority**: GitHub プロバイダーは URL ベースの入力であり、ZIP 配置型とは異なるフロー。使用頻度は低い。

**Independent Test**: `kedro run --params='{"import.provider": "github", "github_url": "https://github.com/rengotaku/rengotaku.github.io/tree/master/test_posts"}'` を実行して Markdown が生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** `import.provider=github` と有効な GitHub URL が指定されている状態, **When** `kedro run` を実行, **Then** リポジトリがクローンされ、Jekyll 記事が Obsidian Markdown として生成される
2. **Given** 無効な URL が指定されている状態, **When** パイプラインを実行, **Then** わかりやすいエラーメッセージが表示される

---

### Edge Cases

- 入力ファイルが 0 件の場合、パイプラインは空の結果で正常終了する
- 会話のメッセージ数が最小閾値（3件）未満の場合、スキップされてログに記録される
- 25,000 文字超の会話はチャンク分割されて複数アイテムとして処理される
- Ollama サーバーが停止している場合、Transform ステージでリトライ後にエラーとなる
- `data/01_raw/` ディレクトリが存在しない場合、適切なエラーメッセージが表示される
- ZIP 内に `conversations.json` が存在しない場合、警告ログを出力してスキップする

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: パイプラインは dispatch 型設計とし、`import.provider` パラメータで適切な Extract パイプラインに振り分けること
- **FR-002**: Claude/OpenAI プロバイダーは `data/01_raw/{provider}/` ディレクトリ内の ZIP ファイルを入力とし、ZIP 直下の `conversations.json` をパースすること
- **FR-003**: Claude Extract ノードは ZIP bytes を受け取り、`conversations.json` を抽出してパースする機能を持つこと（現状の `list[dict]` 入力から変更）
- **FR-004**: OpenAI Extract ノードのカタログ定義を ZIP バイナリ読み込みに対応させること
- **FR-005**: GitHub プロバイダーは URL パラメータ指定で動作し、カタログ定義とノードの入出力が正しく接続されること
- **FR-006**: 全プロバイダーで冪等 Resume が機能し、再実行時に完了済みアイテム（会話単位）がスキップされること
- **FR-007**: 入力がない場合やフォーマットが不正な場合に、わかりやすいエラーメッセージが表示されること
- **FR-008**: カタログ定義（catalog.yml）が全ノードの入出力シグネチャと整合すること
- **FR-009**: 既存のテストが全て引き続きパスすること（テストの入力もZIP形式に更新）

### Key Entities

- **DataCatalog エントリ**: 各プロバイダーの入力データセット定義。Claude/OpenAI は ZIP バイナリ対応、GitHub は URL パラメータ
- **ノード入力シグネチャ**: 各 Extract ノードが期待するデータ型。Claude/OpenAI は `dict[str, Callable]`（PartitionedDataset）、GitHub は `str`（URL）
- **パラメータ**: `parameters.yml` で定義されるランタイム設定。`import.provider` で dispatch 先を制御
- **テストフィクスチャ**: `tests/fixtures/claude_test.zip`（3会話）、`tests/fixtures/openai_test.zip`（3会話）— 実データから抽出済み

## Verification Strategy

### 問題の特定

統合テストが MemoryDataset で直接データを注入しているため、カタログ定義（catalog.yml）とノードシグネチャの型不一致が検出されない。問題は入力層のみであり、Transform / Organize のビジネスロジックは正常。

### テスト戦略

1. **ユニットテスト（ノード単体）**: 各 Extract ノードが ZIP bytes を正しくパースすることを検証。テストフィクスチャ（`claude_test.zip`, `openai_test.zip`）を使用
2. **アウトプット正確性検証（parsed_items）**: Extract ノードの出力を expected output と突き合わせ
   - 生成件数が期待値と一致すること
   - 各 parsed_item に必須フィールド（`item_id`, `source_provider`, `content`, `file_id`, `messages`, `conversation_name`, `created_at`）が存在すること
   - `source_provider` がプロバイダー名と一致すること
   - `messages` の件数が元データと一致すること
   - `content` が空でないこと
   - `is_chunked` がデータサイズに応じた正しい値であること
3. **統合テスト（Ollama モック）**: 全パイプラインの結合を検証。Ollama は既存のモックを継続使用
4. **カタログ整合性テスト**: catalog.yml のデータセット型がノードシグネチャと一致することを検証

### テストフィクスチャ

- `tests/fixtures/claude_test.zip`: 実データから3会話を抽出（各4メッセージ）
- `tests/fixtures/openai_test.zip`: 実データから3会話を抽出（5-11 mapping ノード）
- `tests/fixtures/github_jekyll_post.md`: 既存フィクスチャをそのまま使用
- GitHub テスト用 URL: `https://github.com/rengotaku/rengotaku.github.io/tree/master/test_posts`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `kedro run` が `import.provider=claude` でテスト用 ZIP から正常完了する
- **SC-002**: `kedro run` が `import.provider=openai` でテスト用 ZIP から正常完了する
- **SC-003**: `kedro run` が `import.provider=github` でテスト用 URL から正常完了する
- **SC-004**: 全ての既存テストがパスし続ける（ZIP 入力対応に更新後）
- **SC-005**: 同じ `kedro run` コマンドの再実行で完了済みアイテムがスキップされる（冪等 Resume）

## Assumptions

- ユーザーは `data/01_raw/{provider}/` ディレクトリに手動で ZIP ファイルを配置する
- Claude エクスポート ZIP は直下に `conversations.json` を含む
- OpenAI エクスポート ZIP は直下に `conversations.json` を含む（既存の ChatGPT エクスポート形式）
- Makefile ラッパー（`make import INPUT=... PROVIDER=...`）は本フィーチャーのスコープ外とする
- Claude Extract ノードのビジネスロジック（パース処理）は維持し、入力の受け取り方のみ変更する
- Ollama サーバーはローカルで稼働していることが前提
