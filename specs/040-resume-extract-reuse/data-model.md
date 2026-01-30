# Data Model: Resume モード Extract Output 再利用

**Date**: 2026-01-28
**Feature**: 040-resume-extract-reuse

## Entities

### 1. BasePhaseOrchestrator (New)

Phase 実行の共通基底クラス。Template Method パターンで run() を実装。

**属性**:
| Field | Type | Description |
|-------|------|-------------|
| phase_type | PhaseType (property) | Phase の種類（IMPORT, ORGANIZE） |

**メソッド**:
| Method | Visibility | Description |
|--------|------------|-------------|
| run() | public | Template Method - FW が制御フロー管理 |
| _should_load_extract_from_output() | protected | Extract output の存在確認 |
| _load_extract_items_from_output() | protected | JSONL から ProcessingItem を復元 |
| _run_extract_stage() | abstract | Extract stage 実行（各 Phase が実装） |
| _run_transform_stage() | abstract | Transform stage 実行（各 Phase が実装） |
| _run_load_stage() | abstract | Load stage 実行（各 Phase が実装） |

**状態遷移**: なし（ステートレス）

### 2. ProcessingItem (Existing)

ETL パイプラインで処理されるアイテム。

**属性**:
| Field | Type | Description |
|-------|------|-------------|
| item_id | str | 一意識別子 |
| source_path | Path | 元ファイルのパス |
| current_step | str | 現在の処理ステップ |
| status | ItemStatus | 処理状態 |
| metadata | dict | メタデータ |
| content | str | 元コンテンツ |
| transformed_content | str | 変換後コンテンツ |
| output_path | Path | 出力先パス |
| error | str | エラーメッセージ |

**シリアライズ**: `to_dict()` / `from_dict()` で JSONL に保存・復元

### 3. Extract Output File (New Schema)

Extract stage の出力ファイル。固定ファイル名パターン。

**ファイル名パターン**: `data-dump-{番号4桁}.jsonl`
- 例: `data-dump-0001.jsonl`, `data-dump-0002.jsonl`

**分割ルール**: 1000 レコードごとに新規ファイル作成

**除外パターン**: 以下は Resume 復元対象外
- `steps.jsonl`
- `error_details.jsonl`
- `pipeline_stages.jsonl`

### 4. BaseStage Output Writer (Modified)

BaseStage の _write_output_item() が使用する内部状態。

**新規属性**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| _output_file_index | int | 1 | 現在のファイル番号（1-based） |
| _output_record_count | int | 0 | 現在のファイルに書き込んだレコード数 |
| _max_records_per_file | int | 1000 | ファイルあたりの最大レコード数 |

**状態遷移**:
```
初期状態: _output_file_index=1, _output_record_count=0
  ↓ レコード書き込み
_output_record_count++
  ↓ _output_record_count >= 1000
_output_file_index++, _output_record_count=0
```

## Relationships

```
BasePhaseOrchestrator
    ├── ImportPhase (inherits)
    │       ├── uses → ClaudeExtractor / ChatGPTExtractor / GitHubExtractor
    │       ├── uses → KnowledgeTransformer
    │       └── uses → SessionLoader
    └── OrganizePhase (inherits)
            ├── uses → FileExtractor
            ├── uses → NormalizerTransformer
            └── uses → VaultLoader

BaseStage
    └── _write_output_item() → data-dump-*.jsonl

ProcessingItem
    ├── to_dict() → JSONL record
    └── from_dict() ← JSONL record
```

## Validation Rules

### BasePhaseOrchestrator.run()

1. Phase が EXTRACT, TRANSFORM, LOAD stage を持つこと
2. Extract output の復元時、data-dump-*.jsonl のみを対象とする
3. 破損した JSONL レコードはスキップして継続

### BaseStage._write_output_item()

1. ファイル番号は 1 から開始（0001）
2. ファイル番号は 4 桁ゼロパディング
3. レコード数が 1000 を超えたら次のファイルに切り替え
4. Extract と Transform stage のみで出力（Load は対象外）

### Extract Output File

1. ファイル名は `data-dump-` で開始すること
2. 拡張子は `.jsonl` であること
3. 各行は有効な JSON であること
4. 各行は ProcessingItem の to_dict() 形式であること
