# Feature Specification: ChatGPTExtractor Steps分離リファクタリング

**Feature Branch**: `032-extract-step-refactor`
**Created**: 2026-01-24
**Status**: Draft
**Input**: User description: "OptionAのリファクタリング - ChatGPTExtractor.discover_items() の処理を Steps に分離し、Transform/Load と同様に steps.jsonl 出力を可能にする"

## 背景と目的

### 現状の問題

ChatGPTExtractor の `discover_items()` メソッドが以下の処理を一括で実行しており、BaseStage フレームワークの Step 機構を活用していない：

1. ZIP ファイルの発見・読み込み
2. conversations.json の抽出・パース
3. ChatGPT format → Claude format への変換
4. MIN_MESSAGES によるスキップ判定
5. ProcessingItem の作成

この設計により：
- Extract Stage で `steps.jsonl` が生成されない
- 各処理ステップの実行時間・変化率がトレースできない
- Transform/Load Stage との設計パターンが不一致

### 目的

`discover_items()` を軽量化し、実際の処理を Step クラスに分離することで：
- 全 Stage で一貫した `steps.jsonl` 出力を実現
- パフォーマンス分析・デバッグの可視化を向上
- Claude Extractor と同じ設計パターンに統一

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Stage のステップ別トレース (Priority: P1)

開発者が ChatGPT インポート処理のパフォーマンスを分析するため、Extract Stage の各ステップ（ZIP 読み込み、パース、変換）の処理時間と変化率を `steps.jsonl` で確認できる。

**Why this priority**: これが本リファクタリングの主目的。steps.jsonl 出力がないと、Extract Stage がブラックボックスのまま残り、パフォーマンス問題の特定ができない。

**Independent Test**: debug モードで ChatGPT インポートを実行し、`extract/output/debug/steps.jsonl` が生成され、各ステップの timing_ms、before_chars、after_chars、diff_ratio が記録されていることを確認。

**Acceptance Scenarios**:

1. **Given** ChatGPT エクスポート ZIP ファイル, **When** `make import INPUT=xxx PROVIDER=openai DEBUG=1` を実行, **Then** `extract/output/debug/steps.jsonl` に各ステップのログが JSONL 形式で記録される
2. **Given** steps.jsonl が生成された状態, **When** `make item-trace SESSION=xxx ITEM=xxx` を実行, **Then** Extract Stage のステップも表形式で表示される

---

### User Story 2 - 既存機能の互換性維持 (Priority: P1)

既存の ChatGPT インポート機能が同一の入出力で動作し、最終的な Markdown ファイルが変更前と同じ内容で生成される。

**Why this priority**: リファクタリングにより既存機能が破損すると、ユーザーのワークフローが中断される。互換性は必須要件。

**Independent Test**: リファクタリング前後で同じ ChatGPT エクスポートをインポートし、生成された Markdown ファイルの内容が一致することを確認。

**Acceptance Scenarios**:

1. **Given** ChatGPT エクスポート ZIP ファイル, **When** リファクタリング後のコードでインポート実行, **Then** 生成される Markdown ファイルの title、summary、tags、content が変更前と同一
2. **Given** MIN_MESSAGES 未満の会話を含む ZIP, **When** インポート実行, **Then** 該当会話がスキップされ、スキップ理由が記録される（変更前と同じ挙動）

---

### User Story 3 - Claude Extractor との設計統一 (Priority: P2)

開発者が新しい Extractor（GitHub、Slack 等）を追加する際、Claude Extractor と ChatGPT Extractor が同じ設計パターンに従っているため、実装の参考にできる。

**Why this priority**: 将来の拡張性を担保するが、現時点での機能には直接影響しない。

**Independent Test**: Claude Extractor と ChatGPT Extractor のクラス構造を比較し、discover_items() と steps の責務分担が同じパターンであることを確認。

**Acceptance Scenarios**:

1. **Given** ChatGPTExtractor クラス, **When** クラス定義を確認, **Then** discover_items() は ProcessingItem（content=None）の生成のみを担当
2. **Given** ChatGPTExtractor クラス, **When** steps プロパティを確認, **Then** ZIP 読み込み、パース、変換の各処理が独立した Step クラスとして定義されている

---

### User Story 4 - セッション統計の可視化 (Priority: P2)

開発者がセッションの処理結果を確認する際、session.json を見るだけで各フェーズの成功/失敗件数を把握できる。

**Why this priority**: デバッグと運用監視の効率化に寄与するが、コア機能ではない。

**Independent Test**: インポート完了後の session.json を確認し、phases フィールドに item 数が記録されていることを確認。

**Acceptance Scenarios**:

1. **Given** ChatGPT インポートが完了した状態, **When** session.json を確認, **Then** `phases.import` に `success_count`, `error_count`, `status`, `completed_at` が記録されている
2. **Given** 複数フェーズを実行した状態, **When** session.json を確認, **Then** 各フェーズの統計が個別に記録されている

---

### Edge Cases

- ZIP ファイルが破損している場合：適切なエラーメッセージを出力し、処理を中断
- conversations.json が空の場合：警告ログを出力して正常終了（既存挙動を維持）
- 巨大な ZIP ファイル（1GB 超）の場合：メモリ効率を考慮した処理（既存挙動を維持）
- マルチモーダルコンテンツ（画像・音声）を含む場合：プレースホルダーに変換（既存挙動を維持）
- **フェーズ実行中に例外発生（クラッシュ）した場合**：session.json に `status: "crashed"` と `error` フィールドを記録し、処理を中断

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: ChatGPTExtractor の `discover_items()` は ZIP ファイルの発見と基本メタデータの設定のみを担当し、ProcessingItem.content は None で返す
- **FR-002**: ZIP ファイルの読み込みと conversations.json の抽出は専用の Step クラス（ReadZipStep）で実行する
- **FR-003**: ChatGPT format から Claude format への変換は専用の Step クラス（ConvertFormatStep）で実行する
- **FR-004**: MIN_MESSAGES によるスキップ判定は専用の Step クラス（ValidateMinMessagesStep）で実行する
- **FR-005**: 各 Step は BaseStep を継承し、`process()` メソッドで ProcessingItem を変換する
- **FR-006**: 各 Step の実行後、BaseStage フレームワークにより `steps.jsonl` にログが自動記録される
- **FR-007**: リファクタリング後も、最終的な出力（Markdown ファイル）は変更前と同一であること
- **FR-008**: エラーハンドリングは既存の挙動を維持し、破損 ZIP、空の conversations.json 等を適切に処理する
- **FR-009**: 1:N 展開 Step は BaseStage フレームワークの汎用機能として実装し、Extract Stage だけでなく Transform Stage（item 分割等）でも利用可能とする
- **FR-010**: session.json の `phases` フィールドを拡張し、各フェーズ完了時に item 数（success_count, error_count）とステータスを記録する。例外発生時は `status: "crashed"` と `error` フィールドを含める

### Key Entities

- **ProcessingItem**: パイプラインを流れるデータ単位。Extract Stage では ZIP→会話データ→変換済みデータの変遷を経る
- **Step**: 単一の処理単位を表すクラス。BaseStep を継承し、process() で ProcessingItem を変換
- **StageLogRecord**: steps.jsonl に記録されるログエントリ。timing_ms、before_chars、after_chars、diff_ratio を含む
- **PhaseStats**: session.json に記録されるフェーズ統計。status、success_count、error_count、completed_at、error（例外時のみ）を含む

### Data Flow: BEFORE/AFTER by Step

各 Step での ProcessingItem プロパティの変化を示す。

#### Step 0: discover_items() (リファクタリング後)

ZIP ファイルの発見のみ。content は設定しない。

```
BEFORE: (なし - アイテム生成)

AFTER:
  ProcessingItem:
    item_id: "zip_<hash>"
    source_path: Path("chatgpt_export.zip")
    content: None  ← 空のまま
    metadata:
      source_provider: "openai"
      source_type: "conversation"
    status: PENDING
```

#### Step 1: ReadZipStep (1:1)

ZIP を読み込み、conversations.json を抽出。

```
BEFORE:
  ProcessingItem:
    item_id: "zip_<hash>"
    content: None
    metadata: {source_provider: "openai", ...}

AFTER:
  ProcessingItem:
    item_id: "zip_<hash>"
    content: '{"conversations": [...]}' (raw JSON string)
    metadata:
      source_provider: "openai"
      zip_path: "chatgpt_export.zip"
      extracted_file: "conversations.json"
```

#### Step 2: ParseConversationsStep (1:N 展開)

JSON をパースし、各会話を個別の ProcessingItem に分解。

```
BEFORE:
  ProcessingItem (1個):
    item_id: "zip_<hash>"
    content: '{"conversations": [{...}, {...}, {...}]}'

AFTER:
  ProcessingItem[] (N個):
    [0]:
      item_id: "<conversation_uuid_1>"
      content: {"uuid": "xxx", "name": "会話1", "mapping": {...}}
      metadata:
        conversation_uuid: "xxx"
        conversation_name: "会話1"
        created_at: "2025-06-03"
        parent_item_id: "zip_<hash>"  ← 展開元を追跡
    [1]:
      item_id: "<conversation_uuid_2>"
      content: {"uuid": "yyy", "name": "会話2", "mapping": {...}}
      metadata:
        conversation_uuid: "yyy"
        conversation_name: "会話2"
        ...
    [N-1]:
      ...
```

#### Step 3: ConvertFormatStep (1:1, 各アイテムに適用)

ChatGPT format (mapping tree) を Claude format (messages array) に変換。

```
BEFORE:
  ProcessingItem:
    item_id: "<conversation_uuid>"
    content: {"uuid": "xxx", "mapping": {"node_id": {...}}}
    metadata: {conversation_name: "会話1", ...}

AFTER:
  ProcessingItem:
    item_id: "<conversation_uuid>"
    content: [
      {"sender": "human", "text": "ユーザーメッセージ"},
      {"sender": "assistant", "text": "アシスタント応答"},
      ...
    ]
    metadata:
      conversation_name: "会話1"
      message_count: 15
      format: "claude"
```

#### Step 4: ValidateMinMessagesStep (1:1, 各アイテムに適用)

MIN_MESSAGES 閾値チェック。条件未満はスキップ。

```
BEFORE:
  ProcessingItem:
    item_id: "<conversation_uuid>"
    content: [{sender: "human", ...}, ...]
    metadata: {message_count: 2}
    status: PENDING

AFTER (message_count >= MIN_MESSAGES):
  ProcessingItem:
    status: PENDING  ← 変更なし、次の Stage へ

AFTER (message_count < MIN_MESSAGES):
  ProcessingItem:
    status: SKIPPED
    skip_reason: "Message count (2) below minimum (3)"
```

#### Data Flow Summary

```
discover_items()
    │
    ▼ ProcessingItem (content=None)
ReadZipStep [1:1]
    │
    ▼ ProcessingItem (content=raw JSON)
ParseConversationsStep [1:N]
    │
    ▼ ProcessingItem[] (N個、各 content=conversation dict)
ConvertFormatStep [1:1 each]
    │
    ▼ ProcessingItem[] (各 content=messages array)
ValidateMinMessagesStep [1:1 each]
    │
    ▼ ProcessingItem[] (status=PENDING or SKIPPED)
    │
    ▼ Transform Stage へ
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: debug モードでの ChatGPT インポート後、`extract/output/debug/steps.jsonl` が生成され、3つ以上のステップログが記録されている
- **SC-002**: `make item-trace` コマンドで Extract Stage のステップが表示され、各ステップの timing_ms、diff_ratio が確認できる
- **SC-003**: リファクタリング前後で同一の ChatGPT エクスポートをインポートした結果、生成される Markdown ファイルの内容が 100% 一致する
- **SC-004**: 既存のユニットテスト・統合テストが全て成功する
- **SC-005**: Claude Extractor と ChatGPT Extractor の discover_items() が同じ責務（ファイル発見のみ）を持つ設計パターンに統一される
- **SC-006**: 1:N 展開 Step が BaseStage フレームワークの汎用機能として実装され、Transform Stage でも利用可能な API 設計になっている
- **SC-007**: session.json の `phases` フィールドが dict 形式で、各フェーズの `success_count`, `error_count`, `status`, `completed_at` を含む

## Clarifications

### Session 2026-01-24

- Q: Extract Stage は「item を処理する」ではなく「item を生成する」役割であり、1:N 展開（1 ZIP → N 会話）を行う。現在の BaseStage/BaseStep フレームワークは 1:1 処理モデルのため、discover_items() を Steps に分離することが技術的に困難。どのアプローチを取るか？ → A: Option A - フレームワーク拡張（BaseStage に 1:N 展開対応の新しい Step モデルを追加）
- Q: ChatGPT インポートの 1:N 展開はどのフェーズで発生するか？ → A: Phase 3（JSON パース・分解）で発生。Phase 1-2（ZIP 発見・読み込み）は 1:1、Phase 4（変換）も 1:1
- Q: 1:N 展開機構の設計方針は？ → A: Extract Stage 専用ではなく、Transform Stage でも利用可能な汎用的な設計にする（例：Transform での item 分割シナリオにも対応）

## 前提条件

- BaseStage フレームワークを拡張し、1:N 展開対応の汎用 Step モデルを追加する（破壊的変更なし、後方互換性を維持）
- 1:N 展開機構は Extract Stage 専用ではなく、全 Stage で利用可能な汎用設計とする
- Transform Stage、Load Stage の既存実装は変更しない（既存の 1:1 モデルをそのまま使用、将来 1:N が必要な場合は新機能として利用）
- ImportPhase.run() の外部インターフェースは変更しない

## スコープ外

- Claude Extractor の修正（既に正しい設計パターンに従っている）
- 新しい Extractor の追加
- steps.jsonl のフォーマット変更
- debug モード以外での steps.jsonl 出力
