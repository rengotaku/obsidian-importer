# Feature Specification: ChatGPT エクスポートインポート

**Feature Branch**: `030-chatgpt-import`
**Created**: 2026-01-22
**Status**: Draft
**Input**: User description: "ChatGPT エクスポートファイル (.zip) を Claude インポートと同様の Markdown 形式に変換してロードする"

## Clarifications

### Session 2026-01-22

- Q: Claude互換性保証の設計方針は？ → A: 既存ファイル無変更保証 + ProcessingItem 構造不変
- Q: import後の出力はorganizeで利用可能か？ → A: 明記する（FR-011追加）

## 概要

ChatGPT からエクスポートした ZIP ファイル（OpenAI データエクスポート）を解析し、既存の Claude インポートパイプラインと同じ出力形式（Markdown + frontmatter）で Obsidian ノートを生成する。

### データ形式の違い

| 項目 | Claude | ChatGPT |
|------|--------|---------|
| エクスポート形式 | JSON ファイル | ZIP アーカイブ |
| 会話データ | `conversations` 配列 | `conversations.json` |
| 会話ID | `uuid` | `conversation_id` / `id` |
| メッセージ構造 | `chat_messages[]` | `mapping{}` (tree 構造) |
| ロール | `sender` (human/assistant) | `author.role` (user/assistant/system) |
| タイムスタンプ | ISO 8601 文字列 | Unix timestamp (float) |
| 添付ファイル | 別途管理 | ZIP 内に含む（画像、音声） |

## User Scenarios & Testing

### User Story 1 - 基本インポート (Priority: P1)

ユーザーは ChatGPT エクスポート ZIP ファイルを指定し、会話ごとに Markdown ファイルを生成したい。

**Why this priority**: 最も基本的な機能。これがないと何も始まらない。

**Independent Test**: ZIP ファイルを入力として `make import` を実行し、`load/output/conversations/` に Markdown ファイルが生成される。

**Acceptance Scenarios**:

1. **Given** ChatGPT エクスポート ZIP が `.staging/@llm_exports/openai/` に配置されている, **When** `make import INPUT=... PROVIDER=openai` を実行, **Then** 会話ごとに Markdown ファイルが生成される
2. **Given** 会話に user と assistant のメッセージが含まれている, **When** インポート処理が完了, **Then** Markdown に両者のメッセージが callout 形式で含まれる
3. **Given** 会話のタイトルが日本語, **When** ファイル生成, **Then** ファイル名がタイトルと一致する（sanitized）

---

### User Story 2 - メタデータ抽出 (Priority: P1)

会話から title, summary, tags を LLM で抽出し、frontmatter に含める。

**Why this priority**: Claude インポートとの機能パリティ。ナレッジとしての価値はここで決まる。

**Independent Test**: 生成された Markdown の frontmatter に `title`, `summary`, `tags`, `created`, `source_provider: openai`, `item_id` が含まれる。

**Acceptance Scenarios**:

1. **Given** 会話内容がある, **When** Transform ステージが実行, **Then** Ollama で summary と tags が生成される
2. **Given** ChatGPT の `title` フィールドがある, **When** 抽出処理, **Then** frontmatter の `title` にそのまま使用される
3. **Given** `create_time` が Unix timestamp, **When** 変換処理, **Then** `created: YYYY-MM-DD` 形式に変換される

---

### User Story 3 - 既存パイプライン統合 (Priority: P2)

既存の `import` Phase に ChatGPT プロバイダを追加し、`--provider openai` オプションで切り替える。

**Why this priority**: コード再利用と保守性。新規パイプラインを作らない。

**Independent Test**: `python -m src.etl import --input PATH --provider openai` が動作する。

**Acceptance Scenarios**:

1. **Given** `--provider` オプションなし, **When** JSON ファイルを入力, **Then** 従来通り Claude として処理
2. **Given** `--provider openai`, **When** ZIP ファイルを入力, **Then** ChatGPT として処理
3. **Given** 不正な provider 名, **When** 実行, **Then** エラーメッセージと有効な provider 一覧を表示

---

### User Story 4 - 短い会話のスキップ (Priority: P2)

メッセージ数が閾値未満の会話はスキップする（Claude と同じロジック）。

**Why this priority**: ノイズ削減。短い会話はナレッジとしての価値が低い。

**Independent Test**: メッセージ数 2 以下の会話がスキップされ、ログに記録される。

**Acceptance Scenarios**:

1. **Given** メッセージ数が MIN_MESSAGES 未満, **When** 抽出処理, **Then** スキップされ `skipped_short` としてログに記録
2. **Given** system メッセージのみ, **When** カウント, **Then** system メッセージはカウントに含めない

---

### User Story 5 - 重複検出 (Priority: P2)

`file_id`（ハッシュベース）で重複を検出し、既存ファイルがあれば上書きする。

**Why this priority**: 再インポート時のデータ整合性。

**Independent Test**: 同じ会話を2回インポートしても、1つのファイルのみが存在する。

**Acceptance Scenarios**:

1. **Given** 同一会話の file_id が @index に存在, **When** インポート, **Then** 既存ファイルを上書き
2. **Given** 新規会話, **When** インポート, **Then** 新規ファイルを作成

---

### User Story 6 - 添付ファイル処理 (Priority: P3)

ZIP 内の画像・音声ファイルを適切に処理する。

**Why this priority**: 初期リリースでは必須ではない。テキストのみで MVP を達成。

**MVP Scope**: プレースホルダー実装（`[Image: filename]`, `[Audio: filename]`）。将来的に実ファイル抽出を検討。

**Independent Test**: 添付ファイルがある会話でもエラーにならず、テキスト部分は正常に処理される。

**Acceptance Scenarios**:

1. **Given** 会話に画像参照がある, **When** 抽出処理, **Then** 画像参照をプレースホルダーとして記録（`[Image: filename]`）
2. **Given** 音声ファイルがある, **When** 抽出処理, **Then** 音声参照をプレースホルダーとして記録

---

### Edge Cases

- **空の conversations.json**: 会話数 0 でも正常終了し、警告ログを出力
- **破損した ZIP ファイル**: 適切なエラーメッセージを表示して終了
- **超長い会話**: チャンク分割処理（既存の chunker.py を流用）
- **マルチモーダルコンテンツ**: テキスト部分のみ抽出、画像はプレースホルダー
- **system メッセージ**: 出力から除外（user/assistant のみ）
- **タイムスタンプなし**: 現在日時をフォールバック
- **会話タイトルなし**: 最初のユーザーメッセージから生成

## Requirements

### Functional Requirements

- **FR-001**: System MUST ZIP ファイルを展開して `conversations.json` を読み取る
- **FR-002**: System MUST `mapping` ツリー構造をフラットなメッセージリストに変換する
- **FR-003**: System MUST Unix timestamp を `YYYY-MM-DD` 形式に変換する
- **FR-004**: System MUST `source_provider: openai` を frontmatter に設定する（ChatGPT 会話の識別子）
- **FR-005**: System MUST 既存の Transform/Load ステージを再利用する
- **FR-006**: System MUST `--provider` オプションで Claude/ChatGPT を切り替え可能にする
- **FR-007**: System MUST メッセージ数が MIN_MESSAGES 未満の会話をスキップする
- **FR-008**: System MUST file_id で重複を検出し、上書きする
- **FR-009**: System MUST system ロールのメッセージを出力から除外する
- **FR-010**: System MUST マルチモーダルコンテンツ（画像等）をプレースホルダーとして処理する
- **FR-011**: System MUST organize フェーズで利用可能な形式で Markdown を出力する（`.md` ファイル + YAML frontmatter）

### Claude 互換性保証（設計制約）

以下の制約により、既存の Claude インポート処理への影響がないことを設計レベルで保証する:

- **CC-001**: `claude_extractor.py` は一切変更しない（新規 `chatgpt_extractor.py` を追加）
- **CC-002**: `import_phase.py` への変更は provider 分岐ロジックの追加のみ（既存メソッドの動作変更なし）
- **CC-003**: `ProcessingItem` データクラスの構造（フィールド、型）は変更しない
- **CC-004**: `--provider` オプション未指定時は従来通り Claude として処理（デフォルト動作維持）

**注記**: ProcessingItem の構造変更が必要になった場合は、本 spec を更新し変更理由を明記すること。

### Non-Functional Requirements

- **NFR-001**: 1295 会話のインポートが 2 時間以内に完了する
- **NFR-002**: 既存の Claude インポートテストが引き続きパスする
- **NFR-003**: ZIP 展開は一時ディレクトリで行い、処理後に削除する

### Key Entities

- **ChatGPTConversation**: `conversation_id`, `title`, `create_time`, `update_time`, `mapping`, `current_node`
- **ChatGPTMessage**: `id`, `author.role`, `content.parts[]`, `content.content_type`, `create_time`
- **ProcessingItem**: 既存の ETL モデル（変更なし）

## Success Criteria

### Measurable Outcomes

- **SC-001**: ChatGPT ZIP からの会話インポート成功率 95% 以上
- **SC-002**: 生成された Markdown が Obsidian で正常に表示される
- **SC-003**: frontmatter に必須フィールド（title, summary, tags, created, source_provider, item_id）が含まれる
- **SC-004**: 既存の Claude インポートテストが 100% パスする
- **SC-005**: `make import INPUT=... PROVIDER=openai` で CLI から実行可能

## 技術設計メモ

### 実装方針

1. **新規 Extractor**: `src/etl/stages/extract/chatgpt_extractor.py` を追加
2. **ZIP 処理**: Python 標準ライブラリ `zipfile` を使用
3. **メッセージ順序**: `mapping` ツリーを `parent` → `children` で走査
4. **Transform/Load**: 既存ステージをそのまま再利用
5. **プロバイダ抽象化**: 共通インターフェースで Claude/ChatGPT を切り替え

### ファイル構成（予定）

```
src/etl/
├── stages/
│   └── extract/
│       ├── claude_extractor.py    # 既存
│       └── chatgpt_extractor.py   # 新規
├── phases/
│   └── import_phase.py            # --provider オプション追加
└── cli.py                          # --provider オプション追加
```

### ChatGPT メッセージ走査アルゴリズム

詳細は [plan.md#R1](./plan.md) を参照。`current_node` から `parent` を辿り、逆順でメッセージを収集する。

### 出力フォーマット例

```markdown
---
title: 名刺デザイン改善提案
created: 2026-01-02
summary: ユーザーは名刺のデザイン改善について相談し、ChatGPTは整理・統一感・色使い・フォント・レイアウトについて具体的なアドバイスを提供した。
tags:
  - デザイン
  - 名刺
  - Canva
source_provider: openai
item_id: abc123def456
---

# まとめ

[LLM生成のサマリー]

# 主要な学び

- [学び1]
- [学び2]
```
