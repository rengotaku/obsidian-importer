# Feature Specification: Bonobo & Tenacity ライブラリ導入

**Feature Branch**: `025-bonobo-tenacity-migration`
**Created**: 2026-01-19
**Status**: Draft
**Input**: User description: "https://github.com/python-bonobo/bonobo, https://github.com/jd/tenacity の導入と移行計画。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tenacity によるリトライ機能統一 (Priority: P1)

開発者として、LLM API呼び出しやファイル処理でのリトライロジックを、tenacityライブラリに統一することで、信頼性の高いエラーハンドリングと一貫した挙動を実現したい。

**Why this priority**: 現在、手動実装のリトライロジック（`retry.py`）が存在するが、exponential backoff、jitter、例外ベースのリトライ条件などの高度な機能が不足している。tenacityはこれらを標準でサポートしており、導入の即効性が高い。

**Independent Test**: Ollama API呼び出しにtenacityを適用し、一時的な接続エラーからの回復を確認することで、単独でテスト可能。

**Acceptance Scenarios**:

1. **Given** LLM API呼び出しがタイムアウトした場合, **When** リトライが発生する, **Then** exponential backoff で最大3回まで再試行され、成功すれば正常に処理が継続する
2. **Given** リトライ上限に達した場合, **When** 全試行が失敗する, **Then** 適切なエラーメッセージと共に処理がスキップされ、エラーログに記録される
3. **Given** 既存のリトライ機能を使用しているコード, **When** tenacityに移行する, **Then** 既存のテストが全て通過し、動作に変更がない

---

### User Story 2 - カスタム ETL パイプライン基盤構築 (Priority: P2)

開発者として、llm_import と normalizer のパイプライン処理を、カスタム ETL フレームワーク（Session → Phase → Stage → Step）で再構築することで、処理状態の追跡、テスト容易性の向上を実現したい。

**Why this priority**: 現行パイプラインは動作しているが、ステージ間の依存関係が暗黙的で、処理状態の追跡が困難。カスタム ETL フレームワークは明確な階層構造と JSON ステータス追跡を提供し、長期的なメンテナビリティを向上させる。

**Independent Test**: normalizer の分類判定を Stage として実装し、単一ファイルの分類処理を実行することで、単独でテスト可能。

**Acceptance Scenarios**:

1. **Given** 複数のMarkdownファイル, **When** カスタム ETL パイプラインで処理する, **Then** 現行の run_pipeline_v2 と同等の結果が得られる
2. **Given** パイプライン実行中にエラーが発生した場合, **When** 特定ステージで例外が発生する, **Then** そのファイルのみスキップされ、他のファイル処理は継続する
3. **Given** 大量のファイル処理（100件以上）, **When** パイプラインを実行する, **Then** 並列処理により処理時間が線形ではなく最適化される

---

### User Story 3 - 移行フェーズの段階的実施 (Priority: P3)

開発者として、既存機能を破壊することなく段階的にライブラリを導入することで、リスクを最小化しながら移行を完了したい。

**Why this priority**: 一括移行はリスクが高い。フェーズごとに検証しながら進めることで、問題発生時のロールバックが容易になる。

**Independent Test**: Phase 1（tenacity導入）完了時点で全既存テストが通過することを確認。

**Acceptance Scenarios**:

1. **Given** Phase 1（tenacity導入）完了後, **When** 既存テストを実行する, **Then** 全てのテストが通過する
2. **Given** Phase 2（bonobo導入）完了後, **When** 既存テストを実行する, **Then** 全てのテストが通過する
3. **Given** 移行中に問題が発生した場合, **When** 前フェーズに戻す必要がある, **Then** コードの変更を revert することで即座にロールバック可能

---

### User Story 4 - セッション管理とステータス追跡 (Priority: P1)

開発者として、パイプライン処理の経過をセッションフォルダに記録し、各ファイルの処理ステータスをステップ毎に追跡することで、処理状況の把握とデバッグを容易にしたい。

**Why this priority**: 処理中断時の再開、エラー調査、進捗確認に必須の機能。tenacity と同等の優先度で導入する。

**Independent Test**: 単一ファイルをパイプラインで処理し、@session フォルダにステータス JSON が正しく出力されることを確認。

#### 用語定義（階層構造）

| 用語 | 説明 | 例 |
|------|------|-----|
| **Session** | 処理全体を包含する単位。日付フォルダとして作成 | `20260119_143052/` |
| **Phase** | Session 内の処理種別 | `import/`, `organize/` |
| **Stage** | Phase を ETL パターンで分割したもの | `extract/`, `transform/`, `load/` |
| **Step** | Stage 内の具体的な処理単位 | `parse_json`, `validate`, `generate_metadata` |

#### セッションフォルダ構成

```
.staging/@session/
└── 20260119_143052/                    # Session（日付フォルダ）
    ├── session.json                    # セッションメタデータ
    ├── import/                         # Phase: import
    │   ├── phase.json                  # Phase ステータス
    │   ├── extract/                    # Stage: Extract
    │   │   ├── input/                  # 入力データ（従来の @llm_exports/claude 相当）
    │   │   └── output/                 # 抽出結果
    │   ├── transform/                  # Stage: Transform
    │   │   └── output/                 # 変換結果
    │   └── load/                       # Stage: Load
    │       └── output/                 # 最終出力（従来の @index 相当）
    └── organize/                       # Phase: organize
        ├── phase.json
        ├── extract/
        │   ├── input/                  # 入力データ
        │   └── output/
        ├── transform/
        │   └── output/
        └── load/
            └── output/                 # 最終出力（Vaults への移動候補）
```

**Acceptance Scenarios**:

1. **Given** パイプライン処理を開始する, **When** Session が作成される, **Then** `@session/YYYYMMDD_HHMMSS/` 形式の日付フォルダと `session.json` が作成される
2. **Given** Session が作成された, **When** import Phase を実行する, **Then** `import/` フォルダと `extract/`, `transform/`, `load/` Stage フォルダが作成される
3. **Given** Stage 処理中, **When** 各 Step を通過する, **Then** `phase.json` に処理状態が Step 単位で記録される（モードに関わらず）
4. **Given** debug モードが有効, **When** 処理が進行する, **Then** 各 Stage フォルダに詳細ログファイルが出力される
5. **Given** debug モードが無効, **When** 処理が進行する, **Then** JSON ステータスのみ出力され、詳細ログは出力されない
6. **Given** import Phase の Extract Stage, **When** Claude エクスポートデータを処理する, **Then** `extract/input/` に元データ、`extract/output/` にパース結果が格納される

---

### Edge Cases

- tenacityのリトライがOllama APIの rate limit と競合する場合
  - Assumption: rate limit エラーは専用の wait 戦略（固定待機 + jitter）で対処
- パイプライン移行中に新機能開発が必要になった場合
  - Assumption: 新機能は移行先のアーキテクチャで実装し、旧アーキテクチャへのバックポートは行わない
- セッションフォルダのディスク容量が不足した場合
  - Assumption: 古いセッションフォルダは手動または定期的なクリーンアップで削除する
- 処理中にプロセスが強制終了された場合
  - Assumption: 最後に更新されたステータス JSON から処理状態を復元し、未完了ファイルから再開可能

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは tenacity ライブラリを使用して、LLM API呼び出しのリトライを実装すること
- **FR-002**: リトライ時は exponential backoff（指数バックオフ）と jitter（ランダム遅延）を適用すること
- **FR-003**: リトライ回数は設定可能であり、デフォルトは3回とすること
- **FR-004**: リトライ対象の例外を明示的に指定できること（ConnectionError, TimeoutError など）
- **FR-005**: システムはカスタム ETL フレームワーク（Session → Phase → Stage → Step 階層）を使用してパイプライン処理を実装すること
- **FR-006**: パイプラインの各ステージは独立してテスト可能であること
- **FR-007**: パイプラインはエラー発生時に該当アイテムをスキップし、処理を継続できること
- **FR-008**: 既存の `retry.py` モジュールは tenacity ベースに書き換えること
- **FR-009**: 既存の `run_pipeline_v2` 関数はカスタム ETL パイプライン（src/etl/）に移行すること
- **FR-010**: 移行は段階的に実施し、各フェーズ完了後に全テストが通過すること

#### セッション管理

- **FR-011**: パイプライン実行時、`@session/YYYYMMDD_HHMMSS/` 形式の Session フォルダを作成すること
- **FR-012**: Session フォルダ配下に Phase サブフォルダ（`import/`, `organize/`）を作成すること
- **FR-013**: 各 Phase フォルダ配下に Stage サブフォルダ（`extract/`, `transform/`, `load/`）を作成すること
- **FR-014**: 各 Stage フォルダに `input/` と `output/` サブフォルダを作成すること
- **FR-015**: 処理中の各ファイルのステータスを `phase.json` に Step 単位で記録すること（全モード共通）
- **FR-016**: debug モード有効時、詳細ログを各 Stage フォルダにファイル出力すること
- **FR-017**: debug モード無効時、JSON ステータスのみ出力し、詳細ログは出力しないこと
- **FR-018**: `@index`, `.staging/@llm_exports/claude/parsed` は使用せず、Session フォルダ内で完結すること

#### 実装構成

- **FR-019**: 新規 ETL パイプラインは `src/etl/` フォルダに実装すること
- **FR-020**: 既存の `src/converter/scripts/llm_import/` および `src/converter/scripts/normalizer/` は段階的に `src/etl/` へ移行すること

### Key Entities

- **RetryConfig**: リトライ設定（最大回数、待機時間、対象例外、バックオフ戦略）
- **Session**: 処理全体を包含する単位（セッションID = 日付時刻、開始時刻、Phase 一覧、全体ステータス）
- **Phase**: Session 内の処理種別（import または organize、Phase ステータス、Stage 一覧）
- **Stage**: Phase を ETL パターンで分割したもの（extract/transform/load、入出力パス、Step 一覧）
- **Step**: Stage 内の具体的な処理単位（Step 名、開始/終了時刻、ステータス、エラー情報）
- **ProcessingItem**: パイプラインを流れる処理対象（ファイルパス、コンテンツ、メタデータ、現在 Step）
- **StepResult**: Step 処理結果（成功/失敗、出力データ、エラー情報、処理時間）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: tenacity 導入後、LLM API呼び出しの一時的なエラーからの回復率が向上する（回復可能なエラーの90%以上が自動リトライで回復）
- **SC-002**: カスタム ETL パイプライン移行後、コードの可読性・保守性が向上する（将来目標: 並列化による処理時間短縮）
- **SC-003**: 移行完了後、既存の全テスト（ユニットテスト + 統合テスト）が100%通過する
- **SC-004**: パイプライン処理中のエラー発生時、該当ファイルのみスキップされ、バッチ全体が停止しない
- **SC-005**: 各パイプラインステージを単独でテストでき、テストカバレッジが80%以上を維持する
- **SC-006**: セッションフォルダからステータス JSON を参照することで、処理中断後の再開が可能
- **SC-007**: debug モード有効時、エラー発生箇所の特定に必要な情報がログファイルに記録される

## Assumptions

- tenacity は Python 3.11+ で完全に動作する（ドキュメント確認済み）
- Ollama API のレートリミットは通常の使用パターンでは問題にならない
- 既存テストスイート（unittest）が十分なカバレッジを持ち、移行の検証に使用できる
- 移行は開発者（単一ユーザー）のみが使用するローカル環境で実施され、本番環境への影響はない
