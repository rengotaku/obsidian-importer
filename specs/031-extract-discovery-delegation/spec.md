# Feature Specification: Extract Stage Discovery 委譲

**Feature Branch**: `031-extract-discovery-delegation`
**Created**: 2026-01-23
**Status**: Draft
**Input**: User description: "Extract stage による discover_items 委譲"

## 背景と問題

現在の ETL パイプラインでは、`ImportPhase.discover_items()` が Claude エクスポート形式を前提としており、ChatGPT エクスポートを処理する際に正しくメッセージを抽出できない。

### 現在のアーキテクチャ問題

```
ImportPhase.run():
  1. items = self.discover_items(input_path)  ← Claude 形式のみ対応
  2. extracted = extract_stage.run(ctx, items)
  3. transformed = transform_stage.run(ctx, extracted)
  4. loaded = load_stage.run(ctx, transformed)
```

ChatGPT データは `mapping` ツリー構造でメッセージを保持するが、`ImportPhase._expand_conversations()` は `chat_messages` 配列を期待するため、全ての会話が「メッセージ無し」として処理される。

### 目標アーキテクチャ

```
ImportPhase.run():
  1. extracted = extract_stage.discover_and_run(ctx)  ← 各 Extractor が自分で discover
  2. transformed = transform_stage.run(ctx, extracted)
  3. loaded = load_stage.run(ctx, transformed)
```

## User Scenarios & Testing

### User Story 1 - ChatGPT インポートが正常動作 (Priority: P1)

開発者として、ChatGPT エクスポート ZIP を `make import INPUT=... PROVIDER=openai` で実行した際、全ての会話が正しくメッセージ付きでインポートされることを期待する。

**Why this priority**: 現在の致命的なバグを修正する。ChatGPT インポートが実質的に機能していない状態を解消する。

**Independent Test**: ChatGPT エクスポート ZIP を処理し、出力された Markdown ファイルにメッセージ内容が含まれていることを確認。

**Acceptance Scenarios**:

1. **Given** ChatGPT エクスポート ZIP ファイルがある, **When** `make import INPUT=export.zip PROVIDER=openai` を実行, **Then** 出力ファイルに会話メッセージが正しく含まれる
2. **Given** 1295件の会話を含む ChatGPT エクスポート, **When** インポート実行, **Then** 「メッセージが含まれていません」というファイルが生成されない
3. **Given** ChatGPT の tree 構造 (mapping) を持つ会話, **When** 処理, **Then** メッセージが時系列順に抽出される

---

### User Story 2 - Claude インポートの後方互換性 (Priority: P1)

開発者として、既存の Claude エクスポートインポートが引き続き正常に動作することを期待する。

**Why this priority**: 既存機能の破壊を防ぐ。リグレッションがあってはならない。

**Independent Test**: Claude エクスポートを処理し、現行と同じ出力が得られることを確認。

**Acceptance Scenarios**:

1. **Given** Claude エクスポートフォルダ (conversations.json), **When** `make import INPUT=... PROVIDER=claude` を実行, **Then** 現行と同じ出力ファイルが生成される
2. **Given** 既存の Claude インポートテスト, **When** テスト実行, **Then** 全てのテストがパスする

---

### Edge Cases

- `--provider` オプションが省略された場合、エラーメッセージを表示して終了（provider は必須）
- Extract stage に discover_items() が実装されていない場合、明確なエラーメッセージを表示
- 空の conversations.json/ZIP の場合、警告ログを出力して正常終了（exit 0）
- 混合形式（Claude と ChatGPT が混在）の場合は未サポートとしてエラー

## Requirements

### Functional Requirements

- **FR-001**: 各 Extract stage（ClaudeExtractor, ChatGPTExtractor）は `discover_items()` メソッドを実装しなければならない
- **FR-002**: ImportPhase は Extract stage の `discover_items()` を呼び出してアイテムを取得しなければならない
- **FR-003**: ChatGPTExtractor は `mapping` ツリー構造からメッセージを正しく抽出しなければならない
- **FR-004**: ClaudeExtractor は既存の `chat_messages` 配列形式を引き続きサポートしなければならない
- **FR-005**: 各 Extract stage の discover_items() は Iterator[ProcessingItem] を返さなければならない
- **FR-006**: ImportPhase の既存 discover_items() ロジックは ClaudeExtractor に移動しなければならない
- **FR-007**: `--provider` オプションが省略された場合、明確なエラーメッセージを表示して終了しなければならない

### Key Entities

- **Extract Stage**: 入力データを解析し、ProcessingItem を生成する責務を持つ
- **ProcessingItem**: パイプラインを通過するデータ単位。metadata に source_provider を含む
- **ImportPhase**: 各 Stage を順番に実行するオーケストレーター

## Success Criteria

### Measurable Outcomes

- **SC-001**: ChatGPT インポートで「メッセージが含まれていません」というファイルが 0 件になる
- **SC-002**: 既存の 275 件のユニットテストが全てパスする
- **SC-003**: Claude インポートの出力が変更前と完全に一致する
- **SC-004**: ChatGPT インポートで 95% 以上の会話が正しくメッセージ付きで出力される

## 前提条件

- ChatGPTExtractor.discover_items() は既に ZIP から会話を抽出する実装が存在する
- BaseStage.run() のシグネチャ変更は最小限に抑える
- 既存テストの大規模な書き換えは避ける

## スコープ外

- Provider 自動検出機能は実装しない（`--provider` は常に必須）
- 新しい provider の追加
- Transform/Load stage の変更
