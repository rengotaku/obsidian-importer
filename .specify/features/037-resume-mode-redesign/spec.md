# Feature Specification: Resume モードの再設計

**Feature Branch**: `037-resume-mode-redesign`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "resumeモードの再設計"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 中断したインポートの再開 (Priority: P1)

ユーザーが大量のデータをインポート中にエラーや中断が発生した場合、既に成功した処理をスキップして、未処理のアイテムから処理を再開したい。これにより、LLM 呼び出しの重複コストを回避し、時間を節約できる。

**Why this priority**: Resume モードの核心機能。LLM 呼び出しはコスト（時間・API費用）がかかるため、重複処理を避けることが最も重要な価値。

**Independent Test**: セッション ID のみを指定してコマンドを実行し、既に処理済みのアイテムがスキップされ、未処理のアイテムのみが処理されることを確認する。

**Acceptance Scenarios**:

1. **Given** 10件中5件が処理済みのセッション、**When** `--session SESSION_ID` のみでインポートを実行、**Then** 処理済み5件はスキップされ、未処理5件のみが処理される
2. **Given** 全件が処理済みのセッション、**When** Resume を実行、**Then** 全件スキップされ、新たな LLM 呼び出しは発生しない
3. **Given** 処理済み0件のセッション（全て失敗）、**When** Resume を実行、**Then** 全件が再処理される

---

### User Story 2 - 失敗アイテムの自動リトライ (Priority: P2)

ユーザーが Resume を実行した際、前回失敗したアイテムが自動的にリトライされ、一時的なエラー（ネットワーク障害、LLM タイムアウト等）から回復したい。

**Why this priority**: エラーからの回復は Resume モードの重要な副次機能。ただし、成功アイテムのスキップが先に実装されていないと意味がない。

**Independent Test**: 失敗したアイテムを含むセッションで Resume を実行し、失敗アイテムが再処理されることを確認する。

**Acceptance Scenarios**:

1. **Given** 3件成功、2件失敗のセッション、**When** Resume を実行、**Then** 3件はスキップ、2件は再処理される
2. **Given** LLM タイムアウトで失敗したアイテム、**When** Resume を実行、**Then** リトライにより成功する可能性がある

---

### User Story 3 - クラッシュからの復旧 (Priority: P3)

予期しないクラッシュ（OOM、プロセス強制終了、停電等）が発生しても、次回実行時に中断箇所から処理を再開したい。

**Why this priority**: クラッシュ復旧は Resume モードの発展機能。通常の中断シナリオ（P1, P2）が動作していれば、クラッシュ復旧も同じロジックで対応可能。

**Independent Test**: 処理中にプロセスを強制終了し、再実行時に中断箇所から再開されることを確認する。

**Acceptance Scenarios**:

1. **Given** 100件中50件処理時にクラッシュ、**When** 再起動後に Resume を実行、**Then** 51件目から処理が再開される
2. **Given** ログ書き込み中にクラッシュ、**When** 再起動後に Resume を実行、**Then** 破損したログエントリは無視され、処理が継続される

---

### Edge Cases

- 同一アイテムが複数回ログに記録されている場合、最新のステータスを使用する
- ログファイル（pipeline_stages.jsonl）が破損している場合、読み込み可能な部分のみを使用し、エラーを警告として出力
- ログファイルが存在しない場合、全アイテムを新規として処理する（Resume せず通常実行）
- チャンク分割されたアイテムは、全チャンクが成功した場合のみ「成功」とみなす
- ログに記録されているが入力ファイルに存在しないアイテムは無視する

## Requirements *(mandatory)*

### Functional Requirements

#### Resume モード起動

- **FR-001**: システムは `--session SESSION_ID` のみの指定で Resume モードを実行できなければならない
- **FR-002**: システムはセッションディレクトリから入力ファイルとプロバイダーを自動検出しなければならない

#### ステージ別スキップ戦略

- **FR-003**: Extract ステージは **Stage 単位** でスキップ判定を行わなければならない
  - Extract 出力フォルダに結果が存在すれば、Extract Stage 全体をスキップ
  - 軽量処理（ファイル読み込み、JSON パース）のため、アイテム単位のスキップは不要
- **FR-004**: Transform ステージは **アイテム単位** でスキップ判定を行わなければならない
  - pipeline_stages.jsonl で status="success" のアイテムをスキップ
  - LLM 呼び出しを含む重い処理のため、アイテム単位のスキップが必須
- **FR-005**: Load ステージは **アイテム単位** でスキップ判定を行わなければならない
  - pipeline_stages.jsonl で status="success" のアイテムをスキップ
  - 冪等性があるため、再実行しても問題ないが効率化のためスキップ

#### スキップ判定ロジック

- **FR-006**: システムは処理済みアイテム（status="success"）をスキップしなければならない
- **FR-007**: スキップしたアイテムは pipeline_stages.jsonl に **記録しない**（ログの肥大化を防止）
- **FR-008**: システムは失敗アイテム（status="failed"）を再処理対象として扱わなければならない
- **FR-009**: システムはスキップされたアイテム（status="skipped"）を再処理対象として扱わなければならない
- **FR-010**: システムは item_id を主キーとしてアイテムの処理状態を追跡しなければならない
- **FR-011**: システムはチャンク分割されたアイテムについて、parent_item_id を使用して元の会話を追跡しなければならない

#### ログ出力

- **FR-012**: システムは **常に** 詳細ログを出力しなければならない（CLI の `--debug` フラグを廃止し、詳細ログをデフォルト動作に昇格）
- **FR-013**: ログファイルは **Phase フォルダ直下** に出力しなければならない
  - `{phase}/pipeline_stages.jsonl` - ステージ処理ログ（成功/失敗のみ記録、スキップは記録しない）
  - `{phase}/steps.jsonl` - ステップ詳細ログ
  - `{phase}/error_details.jsonl` - エラー詳細
- **FR-014**: システムはログ読み込み時のエラーを適切に処理し、可能な限り処理を継続しなければならない
- **FR-015**: システムは Resume 実行時の統計をコンソールに報告しなければならない
  - 処理数: 今回実際に処理したアイテム数
  - スキップ数: 入力数 - (成功数 + 失敗数 + 今回処理数) で算出
  - 成功数/失敗数: pipeline_stages.jsonl から取得

### Key Entities

- **ProcessingItem**: パイプラインを流れる処理単位。item_id で一意に識別される
- **StageLogRecord**: pipeline_stages.jsonl の1レコード。ステージ名、item_id、ステータスを含む
- **CompletedItemsCache**: Transform/Load ステージで処理完了したアイテムのセット。スキップ判定に使用

### 責務分離

スキップ判定はフレームワーク層で行い、具象 Step クラスは Resume モードを意識しない。

#### フレームワーク層（Stage / Phase クラス）の責務

- pipeline_stages.jsonl を読み込み、処理済み item_id のセットを構築する
- 各アイテムをループする際にスキップ判定を行う
- スキップ対象のアイテムは Step に渡さない
- 未処理のアイテムのみを Step に渡す

#### 具象層（Step クラス）の責務

- 渡されたアイテムを処理するだけ
- スキップ判定のことは知らない
- Resume モードの存在を意識しない
- 処理ロジックのみに集中する

#### 処理フロー

```
Phase.run():
  completed_items = load_completed_items(pipeline_stages.jsonl)

  for item in input_items:
      if item.item_id in completed_items:
          skip_count += 1
          continue  # Step には渡さない

      for step in steps:
          item = step.process(item)  # Step は未処理アイテムのみ受け取る

      write_to_log(item)  # 成功/失敗のみ記録
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 処理済みアイテムに対する LLM 呼び出しが発生しない（コスト削減率100%）
- **SC-002**: Resume 実行時間は「未処理アイテム数 × 平均処理時間」に比例する（処理済みアイテム数に依存しない）
- **SC-003**: 1000件のログファイルからの処理済みアイテム読み込みが1秒以内に完了する
- **SC-004**: クラッシュ後の Resume 実行で、重複処理されるアイテムが1件以下である
- **SC-005**: Resume 実行後の統計（成功/失敗/スキップ）が実際の処理結果と一致する

## ETL ステージ別 Resume 戦略

### 処理コストとスキップ戦略

| ステージ | 処理内容 | コスト | スキップ単位 | 理由 |
|---------|---------|--------|------------|------|
| Extract | ファイル読み込み、JSON パース | 低（LLM なし） | Stage 単位 | 軽量なので再実行でも問題ない |
| Transform | LLM 呼び出し、知識抽出 | **高**（LLM あり） | アイテム単位 | コスト削減の主要ターゲット |
| Load | ファイル書き込み | 低 | アイテム単位 | 効率化のため |

### Resume シナリオ別動作

| シナリオ | Extract | Transform | Load |
|---------|---------|-----------|------|
| Extract 途中で中断 | 再実行 | 新規実行 | 新規実行 |
| Transform 途中で中断 | **Stage スキップ** | アイテム単位スキップ | 新規実行 |
| Load 途中で中断 | **Stage スキップ** | **Stage スキップ** | アイテム単位スキップ |
| 全完了後に Resume | **Stage スキップ** | **Stage スキップ** | **Stage スキップ** |

## フォルダ構造

```
.staging/@session/YYYYMMDD_HHMMSS/
├── session.json
└── import/                          # Phase
    ├── phase.json
    ├── pipeline_stages.jsonl        # ステージ処理ログ（Phase 直下）
    ├── steps.jsonl                  # ステップ詳細ログ（Phase 直下）
    ├── error_details.jsonl          # エラー詳細（Phase 直下）
    ├── extract/
    │   ├── input/
    │   └── output/
    ├── transform/
    │   └── output/
    └── load/
        └── output/
```

## Assumptions

- pipeline_stages.jsonl は常にアペンド（追記）モードで書き込まれる
- item_id はセッション内で一意である
- ログファイルのサイズは通常数千〜数万レコード程度である
- 同一セッションの Resume は複数回実行される可能性がある
- Extract は軽量処理のため、再実行のコストは許容範囲内である
