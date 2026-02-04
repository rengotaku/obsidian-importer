# Feature Specification: 柔軟な入出力比率対応フレームワーク

**Feature Branch**: `028-flexible-io-ratios`
**Created**: 2026-01-20
**Status**: Draft
**Input**: User description: "1:1、1:N に対応したフレームワーク設計。また各比率毎にdebug時のログが正しく出力される。"

## Clarifications

### Session 2026-01-20

- Q: 1:1と1:Nではログの出力形式は同じになるか？ → A: 同一形式（両方とも同じJSONLスキーマ）
- Q: FW側で自動的にログを出力するようになるか？ → A: 自動出力（BaseStage.run()内で自動的にdebugログを出力）
- Q: 継承側ではログ出力を操作させないようになるか？ → A: 完全禁止（継承クラスはログ出力を一切カスタマイズできない）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 標準的な1:1処理（現状維持） (Priority: P1)

開発者として、1つの入力アイテムを1つの出力アイテムに変換する標準的なETL処理を行いたい。これは最も一般的なユースケースであり、既存の動作を維持する必要がある。

**Why this priority**: 現在のETLパイプラインの基本動作であり、既存機能の後方互換性を保証するため最優先。

**Independent Test**: 単一のJSONファイルを処理し、単一のMarkdownファイルが出力されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 1つの会話JSONファイルがExtract Stageの入力にある, **When** パイプラインを実行する, **Then** 対応する1つのMarkdownファイルがLoad Stageの出力に生成される
2. **Given** debugモードが有効, **When** 1:1処理を実行する, **Then** 各Step毎にJSONLファイルがdebugフォルダに出力される
3. **Given** 1:1処理が完了, **When** pipeline_stages.jsonlを確認する, **Then** 入力ファイル名と出力ファイル名の対応が1対1で記録されている

---

### User Story 2 - 1:N展開処理（チャンク分割） (Priority: P1)

開発者として、1つの大きな入力アイテムを複数の出力アイテムに展開したい。例えば、25000文字を超える会話を複数のチャンクファイルに分割する場合に使用する。

**Why this priority**: 大規模会話の処理に必須の機能であり、現在の課題（KnowledgeTransformerが独自run()を実装している問題）を解決するため同率最優先。

**Independent Test**: 30000文字の会話ファイルを処理し、2つ以上のチャンクMarkdownファイルが出力されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 25000文字を超える会話JSONファイル, **When** パイプラインを実行する, **Then** 複数のチャンクMarkdownファイルが生成される（例: `uuid_001.md`, `uuid_002.md`）
2. **Given** 1:N展開が発生し、debugモードが有効, **When** 処理を実行する, **Then** 元の入力1件に対して、展開された各出力アイテム毎にStep単位のdebugログが出力される
3. **Given** 1:N展開が完了, **When** pipeline_stages.jsonlを確認する, **Then** 元の入力ファイル名と展開された各出力ファイル名の対応関係が追跡可能な形式で記録されている

---

### Edge Cases

- **空の入力**: 入力アイテムが0件の場合、エラーなく処理が完了し、出力も0件となる
- **展開失敗**: 1:N展開中に一部のチャンクが失敗した場合、成功したチャンクは出力され、失敗したチャンクはエラーログに記録される
- **単一メッセージが閾値超過**: 1つのメッセージだけで25000文字を超える場合、分割せずに単独チャンクとして処理される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: フレームワークはStep単位で1:1（1入力→1出力）処理をサポートしなければならない
- **FR-002**: フレームワークはStep単位で1:N（1入力→複数出力）展開処理をサポートしなければならない
- **FR-003**: debugモード有効時、1:1および1:N両方で同一のJSONLスキーマを使用してdebugログを出力しなければならない
- **FR-004**: debugログは`output/debug/step_{番号}_{step名}/`フォルダにJSONL形式で出力されなければならない
- **FR-005**: pipeline_stages.jsonlは入出力の対応関係を追跡可能な形式で記録しなければならない
- **FR-006**: 継承クラスはBaseStageの`run()`メソッドをオーバーライドせずに入出力比率パターンを実現できなければならない
- **FR-007**: 1:N展開時、元の入力アイテムと展開後の各出力アイテムの親子関係がメタデータに記録されなければならない
- **FR-008**: debugログ出力はBaseStage.run()内で自動的に実行されなければならない（継承クラスでの明示的呼び出し不要）
- **FR-009**: 継承クラスはdebugログ出力の形式・出力先・タイミングを一切カスタマイズできてはならない

### Key Entities

- **ProcessingItem**: パイプラインを流れる処理単位。チャンク分割時はmetadataに親子関係を保持
- **StepDebugRecord**: Step毎のdebug出力レコード。1:1/1:N共通の統一スキーマで記録
- **StageLogRecord**: pipeline_stages.jsonlのレコード。チャンク追跡フィールドを含む

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 全ての入出力比率パターン（1:1, 1:N）でパイプラインが正常完了する
- **SC-002**: debugモード有効時、全てのStepで各処理アイテム毎にdebugログファイルが自動生成される
- **SC-003**: 継承クラスでBaseStage.run()をオーバーライドする必要がなくなる（コード重複率0%）
- **SC-004**: 25000文字超の会話が自動的にチャンク分割され、各チャンクが個別に処理される
- **SC-005**: pipeline_stages.jsonlから任意の出力ファイルに対して、元の入力ファイルを特定できる
- **SC-006**: 既存のテストが全て通過する（後方互換性100%）
- **SC-007**: 1:1と1:Nのdebugログが同一スキーマで出力され、同一ツールで解析可能である

## Assumptions

- 1:N展開の閾値は現行の25000文字を維持する
- debugログの出力形式はJSONL（1行1JSON）を維持する
- チャンク分割はメッセージ境界で行い、オーバーラップを2メッセージ設ける（現行仕様維持）
