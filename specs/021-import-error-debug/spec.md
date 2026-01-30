# Feature Specification: LLMインポート エラーデバッグ改善

**Feature Branch**: `021-import-error-debug`
**Created**: 2026-01-17
**Status**: Draft
**Input**: User description: "LLMインポート処理のエラーログ改善: JSONパースエラー発生時に原文とLLM出力を@plan配下にファイル出力する機能を追加。また@planフォルダの整理（古いセッション削除、構造改善）も含める"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - エラー原因の特定 (Priority: P1)

開発者として、LLMインポート処理でJSONパースエラーが発生した際に、エラーの原因を特定したい。現状ではエラーメッセージのみが表示され、実際のLLM出力内容を確認できないため、問題の根本原因を特定できない。

**Why this priority**: エラーの原因を特定できなければ、修正も再試行もできない。デバッグ作業の最重要ステップ。

**Independent Test**: エラー発生時に出力されるファイルを確認し、原文とLLM出力が正しく保存されていることを検証できる。

**Acceptance Scenarios**:

1. **Given** JSONパースエラーが発生した会話がある, **When** インポート処理を実行する, **Then** エラー詳細ファイルが `@plan/import/{session_id}/errors/` 配下に出力される
2. **Given** エラー詳細ファイルが存在する, **When** ファイルを開く, **Then** 元の会話内容、LLMへのプロンプト、LLMの生の出力が確認できる
3. **Given** 複数のエラーが発生した, **When** エラーファイルを確認する, **Then** 各エラーが個別のファイルとして整理されている

---

### User Story 2 - @planフォルダの構造改善 (Priority: P1)

開発者として、`@plan` フォルダの構造を改善し、目的別にファイルを整理したい。現状ではセッションログ、テスト結果、エラーログが混在している。

**Why this priority**: エラーデバッグ・中間ファイル保持のベースとなるフォルダ構造。

**Independent Test**: 新しいフォルダ構造でファイルが正しく配置されることを検証できる。

**Acceptance Scenarios**:

1. **Given** 新しい構造が定義されている, **When** インポート処理を実行する, **Then** ファイルが `@plan/import/{session_id}/` に配置される
2. **Given** 新しい構造が定義されている, **When** organize処理を実行する, **Then** ファイルが `@plan/organize/{session_id}/` に配置される

---

### User Story 3 - 中間ファイルの保持 (Priority: P1)

開発者として、処理の各段階で生成されるファイルを保持したい。Phase 1（JSON→Markdown変換）とPhase 2（ナレッジ抽出）の出力を残すことで、問題発生時のデバッグや処理の検証が可能になる。

**Why this priority**: エラーデバッグと同様に重要。中間ファイルがないと処理の追跡が困難。

**Independent Test**: インポート処理後に中間ファイルが保持されていることを確認できる。

**Acceptance Scenarios**:

1. **Given** Phase 1が完了した, **When** @plan/import/{session_id}/parsed/ を確認する, **Then** 変換されたMarkdownファイルが保持されている
2. **Given** Phase 2が完了した, **When** @plan/import/{session_id}/output/ を確認する, **Then** 生成されたナレッジファイルが保持されている
3. **Given** @indexへの移動が成功した, **When** 中間ファイルを確認する, **Then** parsed/ と output/ の両方が削除されずに残っている

---

### Edge Cases

- エラーファイルの書き込み中にディスク容量が不足した場合の処理
- 同一会話で複数回エラーが発生した場合のファイル名衝突回避
- LLM出力が極端に大きい場合の対応（トランケーション）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST JSONパースエラー発生時に、エラー詳細ファイルを出力する
- **FR-002**: System MUST エラー詳細ファイルに以下を含める：元の会話内容、LLMプロンプト、LLMの生の出力、エラーメッセージ、エラー位置
- **FR-003**: System MUST エラーファイルを `@plan/import/{session_id}/errors/` 配下に保存する
- **FR-004**: System MUST 新規ファイルを目的別サブフォルダに配置する（organize/, import/, test/）
- **FR-005**: System MUST Phase 1出力（parsed）を `@plan/import/{session_id}/parsed/` に保持する
- **FR-006**: System MUST Phase 2出力（@index移動前）を `@plan/import/{session_id}/output/` に保持する
- **FR-007**: System MUST 中間ファイル（parsed, output）を自動削除しない

### Key Entities

- **ErrorDetail**: エラー発生時の詳細情報（会話ID、元コンテンツ、LLMプロンプト、LLM出力、エラー種別、エラー位置、タイムスタンプ）
- **Session**: インポートセッション（セッションID、開始時刻、終了時刻、処理件数、成功/失敗数）
- **IntermediateFile**: 中間ファイル（元会話ID、生成ナレッジファイル名、生成時刻、@indexへの移動状態）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: JSONパースエラー発生時、100%のケースでエラー詳細ファイルが出力される
- **SC-002**: エラー詳細ファイルから、開発者が3分以内にエラー原因を特定できる
- **SC-003**: @planフォルダのサブフォルダ構造により、目的のファイルを5秒以内に特定できる
- **SC-004**: インポート処理後、100%のケースで中間ファイルが保持される

## Assumptions

- エラーファイルのサイズ上限は10MBとする（超過時はトランケーション）
- 既存の `import_*`, `test_*` フォルダは現状維持（マイグレーションは今回スコープ外）
- クリーンアップ機能は今回スコープ外（将来の拡張として検討）

## Proposed Folder Structure

```
@plan/
├── organize/              # /og:organize 処理ログ
│   └── {session_id}/
├── import/                # /og:import-claude 処理ログ
│   └── {session_id}/
│       ├── parsed/        # Phase 1出力（JSON→Markdown変換結果）
│       │   └── conversations/
│       │       └── {conversation_title}.md
│       ├── output/        # Phase 2出力（@index移動前の中間ファイル）
│       │   └── {knowledge_file}.md
│       ├── errors/        # エラー詳細ファイル
│       │   └── {conversation_id}.md
│       └── session.json   # セッション情報
└── test/                  # テスト実行ログ
    └── {session_id}/
```

### 現在の構造との対応

| 現在の場所 | 新しい場所 |
|-----------|-----------|
| `@llm_exports/claude/parsed/conversations/` | `@plan/import/{session}/parsed/conversations/` |
| `@index/` (処理完了前) | `@plan/import/{session}/output/` |
| `@plan/import_*` | `@plan/import/{session}/` |
| `@plan/test_*` | `@plan/test/{session}/` |
