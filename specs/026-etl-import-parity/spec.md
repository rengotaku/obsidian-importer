# Feature Specification: ETL Import パリティ実装

**Feature Branch**: `026-etl-import-parity`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "src/etl の import 処理を src/converter と同等にする - Ollama 知識抽出、file_id 生成、チャンク分割、英語 Summary 翻訳、@index 出力、エラー詳細ファイル出力を実装"

## 概要

src/etl の Import Phase を src/converter/scripts/llm_import と機能的に同等にする。現在 src/etl は基本的なフレームワークのみ実装されており、核心機能（Ollama 知識抽出、file_id、チャンク分割など）がスタブ状態。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ollama を使った知識抽出 (Priority: P1)

ユーザーは Claude 会話エクスポートから、Ollama を使って要約・タグ・コードスニペットを自動抽出し、構造化されたナレッジノートを生成したい。

**Why this priority**: これが import 処理の核心機能。知識抽出なしでは会話データを単にコピーするだけになり、ナレッジベースとしての価値がない。

**Independent Test**: 1つの会話 JSON を入力し、Ollama で処理された要約・タグ付きの Markdown ファイルが出力されることを確認。

**Acceptance Scenarios**:

1. **Given** 会話データを含む JSON ファイル, **When** import を実行, **Then** Ollama が呼び出され、要約・タグ・コードスニペットが抽出される
2. **Given** 抽出されたデータ, **When** Markdown 生成, **Then** frontmatter に title, uuid, created, tags が含まれ、本文に要約とコードスニペットが含まれる
3. **Given** Ollama がエラーを返す, **When** import を実行, **Then** エラーが記録され、アイテムは FAILED ステータスになる

---

### User Story 2 - file_id によるファイル追跡 (Priority: P1)

ユーザーは、ファイルの移動や名前変更後も同一ファイルを追跡できるよう、コンテンツベースの一意な ID を各ファイルに付与したい。

**Why this priority**: file_id がないとファイルの重複検出や更新追跡ができず、再処理時に同じファイルを何度も処理してしまう。

**Independent Test**: 同じ会話を2回処理し、2回目は「処理済み」としてスキップされることを確認。

**Acceptance Scenarios**:

1. **Given** 新規会話, **When** 処理完了, **Then** file_id が frontmatter に付与される（12文字の16進数ハッシュ）
2. **Given** file_id 付きファイル, **When** 再度 import 実行, **Then** 処理済みとしてスキップされる
3. **Given** Phase 1 で生成された file_id, **When** Phase 2 処理, **Then** 同じ file_id が継承される

---

### User Story 3 - 大規模会話のチャンク分割 (Priority: P2)

ユーザーは、大規模な会話（メッセージ数が多い、または長い）を適切なサイズに分割し、それぞれ個別のナレッジノートとして出力したい。

**Why this priority**: Ollama にはコンテキスト長制限があり、大規模会話を一度に処理するとエラーになる。分割処理は安定性に必須。

**Independent Test**: 100メッセージ以上の会話を処理し、複数のチャンクファイルが生成されることを確認。

**Acceptance Scenarios**:

1. **Given** メッセージ数が閾値を超える会話, **When** import 実行, **Then** 複数のチャンクに分割され、各チャンクが個別ファイルとして出力される
2. **Given** チャンク分割された会話, **When** 全チャンク処理完了, **Then** 各チャンクに異なる file_id が付与される
3. **Given** 一部チャンクが失敗, **When** import 完了, **Then** 成功したチャンクは保存され、失敗したチャンクのみエラー記録される

---

### User Story 4 - 英語 Summary の自動翻訳 (Priority: P2)

ユーザーは、Claude が生成した英語の Summary を日本語に自動翻訳し、日本語ナレッジベースとの一貫性を保ちたい。

**Why this priority**: 日本語ナレッジベースに英語 Summary が混在すると検索性・可読性が低下する。

**Independent Test**: 英語 Summary 付きの会話を処理し、翻訳された日本語 Summary が出力されることを確認。

**Acceptance Scenarios**:

1. **Given** 英語 Summary を持つ会話, **When** import 実行, **Then** Summary が日本語に翻訳される
2. **Given** 日本語 Summary を持つ会話, **When** import 実行, **Then** Summary はそのまま使用される
3. **Given** 翻訳エラー発生, **When** import 実行, **Then** 元の英語 Summary を使用し、警告をログ出力

---

### User Story 5 - @index への最終出力 (Priority: P2)

ユーザーは、処理完了したファイルを最終出力先（@index フォルダ）にコピーし、後続の整理処理（organize）で利用可能にしたい。

**Why this priority**: セッションフォルダのみへの出力では、後続処理との連携ができない。

**Independent Test**: import 完了後、@index フォルダに同じファイルが存在することを確認。

**Acceptance Scenarios**:

1. **Given** 処理成功したアイテム, **When** Load Stage 完了, **Then** session/output と @index の両方にファイルが出力される
2. **Given** 同名ファイルが @index に存在, **When** 新規出力, **Then** file_id で重複判定し、異なれば新規作成、同じなら更新

---

### User Story 6 - エラー詳細ファイル出力 (Priority: P3)

ユーザーは、処理失敗時に詳細なデバッグ情報（元の会話、LLM プロンプト、生レスポンス）をファイルとして保存し、問題調査を容易にしたい。

**Why this priority**: エラーログだけでは原因特定が困難。デバッグ情報があれば再現・修正が容易。

**Independent Test**: 意図的にエラーを発生させ、errors/ フォルダに詳細ファイルが出力されることを確認。

**Acceptance Scenarios**:

1. **Given** Ollama 抽出エラー発生, **When** エラー処理, **Then** errors/ フォルダに詳細ファイルが出力される
2. **Given** エラー詳細ファイル, **When** 内容確認, **Then** session_id, conversation_id, error_type, error_message, original_content, llm_prompt, llm_output が含まれる

---

### User Story 8 - DEBUG モード Step 毎差分出力 (Priority: P2)

ユーザーは、DEBUG モード時に各 Step の処理結果を Markdown ファイルとして出力し、Step 間の変化を比較・確認したい。

**Why this priority**: Step 毎の変化が可視化されることで、どの Step で問題が発生したか特定しやすくなる。

**Independent Test**: DEBUG モードで import 実行後、各 Step フォルダに全アイテムの Markdown ファイルが存在することを確認。

**Acceptance Scenarios**:

1. **Given** DEBUG モード有効, **When** import 実行, **Then** extract/input/ に入力ファイルが出力される
2. **Given** DEBUG モード有効, **When** 各 Step 完了, **Then** step_{name}/ フォルダに処理後の Markdown が出力される
3. **Given** DEBUG モード有効, **When** Load Stage 完了, **Then** load/output/ に最終出力が存在する
4. **Given** 通常モード, **When** import 実行, **Then** 中間 Step フォルダは作成されない
5. **Given** Step A → Step B の順で処理, **When** 差分確認, **Then** Step A の出力と Step B の出力を比較して変化がわかる

**DEBUG モード時のフォルダ構成**:

```
import/
├── phase.json
├── extract/
│   ├── input/                         # 元の入力
│   │   └── {item_id}.md
│   ├── step_parse_json/               # Step 完了後
│   │   └── {item_id}.md
│   └── step_validate/
│       └── {item_id}.md
├── transform/
│   ├── step_extract_knowledge/
│   │   └── {item_id}.md
│   ├── step_generate_metadata/
│   │   └── {item_id}.md
│   └── step_format_markdown/
│       └── {item_id}.md
└── load/
    ├── step_write_to_session/
    │   └── {item_id}.md
    └── output/                        # 最終出力
        └── {item_id}.md
```

---

### User Story 7 - パイプライン処理ログ（JSONL）自動出力 (Priority: P2)

ユーザーは、各ファイルの各ステージ（Extract/Transform/Load）の処理状態・タイミングを JSONL 形式で自動記録し、処理フローの可視化・分析を行いたい。Step 実装者は明示的なログ出力コードを書く必要がない。

**Why this priority**: phase.json だけでは個別ファイルの処理詳細が不明。JSONL 形式なら処理順序・タイミングが明確で、後から分析可能。フレームワーク自動出力により実装負荷も軽減。

**Independent Test**: import 実行後、pipeline_stages.jsonl が存在し、各ファイルの各ステージのレコードが含まれることを確認。Step 実装にログ出力コードがないことを確認。

**Acceptance Scenarios**:

1. **Given** 複数ファイルを処理, **When** import 完了, **Then** pipeline_stages.jsonl に各ファイル×各ステージのレコードがフレームワークにより自動追記される
2. **Given** 処理成功したステージ, **When** BaseStage.run() 完了, **Then** timestamp, filename, stage, timing_ms, file_id が自動記録される
3. **Given** スキップされたステージ, **When** item.status == SKIPPED, **Then** skipped_reason が自動記録される
4. **Given** Transform ステージ完了, **When** content サイズ変化あり, **Then** before_chars, after_chars, diff_ratio が自動計算・記録される
5. **Given** Step 実装, **When** process() メソッド作成, **Then** ログ出力コードは不要（metadata 設定のみ）

---

### Edge Cases

- 会話メッセージ数が MIN_MESSAGES（3件）未満の場合 → スキップ、skip_reason を記録
- Ollama が応答しない（タイムアウト）場合 → リトライ後、FAILED ステータスに
- JSON パースエラー（不正な Ollama レスポンス）の場合 → エラー詳細ファイルに raw_response を保存
- file_id 生成時にファイルパスが存在しない場合 → コンテンツのみからハッシュ生成
- チャンク分割で全チャンクが失敗した場合 → 全体を FAILED とし、エラー記録

## Requirements *(mandatory)*

### Functional Requirements

#### Extract Stage

- **FR-001**: System MUST conversations.json から個別の会話を展開する
- **FR-002**: System MUST メッセージ数が MIN_MESSAGES 未満の会話をスキップし、skip_reason を記録する
- **FR-003**: System MUST 処理済み会話（file_id で判定）をスキップする

#### Transform Stage

- **FR-004**: System MUST Ollama を呼び出し、会話から要約・タグ・コードスニペットを抽出する
- **FR-005**: System MUST 抽出結果を KnowledgeDocument 形式に構築する
- **FR-006**: System MUST 英語 Summary を検出し、日本語に翻訳する
- **FR-007**: System MUST チャンク分割が必要な会話を判定し、25000文字を閾値として分割する
- **FR-008**: System MUST file_id をコンテンツ + 相対パスから生成する（SHA256 ベース、12文字16進数）
- **FR-009**: System MUST Ollama エラー時にリトライを実行する（tenacity 統合）
- **FR-010**: System MUST Markdown フォーマットで出力を生成する（frontmatter + 要約 + コードスニペット）

#### Load Stage

- **FR-011**: System MUST session/output フォルダにファイルを出力する
- **FR-012**: System MUST @index フォルダにもファイルをコピーする
- **FR-013**: System MUST phase.json にステップ単位の処理結果を記録する
- **FR-014**: System MUST エラー発生時に errors/ フォルダに詳細ファイルを出力する

#### Logging（フレームワーク自動出力）

- **FR-015**: フレームワーク（BaseStage）MUST 各アイテムの処理完了時に自動で pipeline_stages.jsonl に追記する
- **FR-016**: フレームワーク MUST 各レコードに timestamp, filename, stage, timing_ms を自動計測・記録する
- **FR-017**: フレームワーク MUST 処理成功時は file_id を、スキップ時は skipped_reason を自動記録する
- **FR-018**: フレームワーク MUST content サイズの変化（before_chars, after_chars, diff_ratio）を自動計算・記録する
- **FR-019**: Step 実装者は ProcessingItem の metadata にログ用情報を設定するだけでよい（明示的なログ出力不要）

#### DEBUG モード Step 毎出力（フレームワーク自動出力）

- **FR-020**: フレームワーク MUST DEBUG モード時、Extract Stage 開始前に extract/input/ へ入力ファイルを出力する
- **FR-021**: フレームワーク MUST DEBUG モード時、各 Step 完了後に step_{name}/ へ Markdown を出力する
- **FR-022**: フレームワーク MUST DEBUG モード時、Load Stage 完了後に load/output/ へ最終出力を出力する
- **FR-023**: フレームワーク MUST 通常モード時、中間 Step フォルダを作成しない
- **FR-024**: Step 実装者は DEBUG 出力のためのコードを書く必要がない（フレームワークが自動処理）

### Key Entities

- **ProcessingItem**: パイプラインを流れるアイテム（item_id, source_path, content, transformed_content, output_path, status, error, metadata）
- **KnowledgeDocument**: 抽出されたナレッジ（title, summary, tags, code_snippets, file_id）
- **ExtractionResult**: Ollama 抽出結果（success, document, error, raw_response, user_prompt）
- **ErrorDetail**: エラー詳細（session_id, conversation_id, error_type, error_message, original_content, llm_prompt, llm_output）
- **StageLogRecord**: パイプライン処理ログ（timestamp, filename, stage, timing_ms, skipped_reason, file_id, before_chars, after_chars, diff_ratio）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: src/converter で処理可能な全ての会話データが、src/etl でも同等の品質で処理される
- **SC-002**: 既存テスト（src/converter/scripts/llm_import/tests/）と同等のテストが src/etl/tests/ でパスする
- **SC-003**: 処理済みファイルの file_id が src/converter と同じアルゴリズムで生成される
- **SC-004**: エラー発生時、デバッグに必要な情報が errors/ フォルダに保存される
- **SC-005**: 大規模会話（100メッセージ以上）がチャンク分割されて正常に処理される
- **SC-006**: 英語 Summary が日本語に翻訳されて出力される
- **SC-007**: pipeline_stages.jsonl が src/converter と同じフォーマットで出力される
- **SC-008**: DEBUG モード時、各 Step の出力が step_{name}/ フォルダに保存され、差分比較が可能

## Assumptions

- Ollama はローカルで稼働しており、エンドポイントにアクセス可能
- src/converter/scripts/llm_import/prompts/ のプロンプトテンプレートを src/etl/prompts/ にコピーする
- src/converter/scripts/llm_import/common/ の必要なモジュールを src/etl/utils/ にコピーして使用（converter への依存を排除）
- MIN_MESSAGES のデフォルト値は 3（src/converter と同じ）
- チャンク分割の閾値は src/converter の should_chunk() ロジックを踏襲（25000文字）

## Out of Scope

- organize Phase の実装（別フィーチャー）
- 新しいプロバイダー（ChatGPT、Gemini など）の追加
- Ollama 以外の LLM バックエンド対応
- GUI / Web インターフェース
