# Data Model: Vault配下ファイル階層化

**Date**: 2026-01-15
**Feature**: 013-vault-hierarchy

## Entities

### 1. Vault

知識領域の最上位コンテナ。

| Field | Type | Description |
|-------|------|-------------|
| name | string | Vault名（エンジニア, ビジネス, 経済, 日常, その他） |
| path | Path | Vaultディレクトリのパス |
| subfolders | list[Subfolder] | 配下のサブフォルダ一覧 |
| root_files | list[MarkdownFile] | ルート直下のファイル一覧 |

### 2. Subfolder

Vault内のトピック別ディレクトリ。

| Field | Type | Description |
|-------|------|-------------|
| name | string | フォルダ名（例: Docker, AWS学習） |
| path | Path | フォルダのパス |
| file_count | int | 配下のファイル数 |
| is_new | bool | 今回新規作成されるか |

### 3. MarkdownFile

分類対象のMarkdownファイル。

| Field | Type | Description |
|-------|------|-------------|
| name | string | ファイル名（拡張子なし） |
| path | Path | 現在のファイルパス |
| title | string | frontmatterのtitle |
| tags | list[string] | frontmatterのtags |
| content_preview | string | 本文先頭2000文字 |
| normalized | bool | 正規化済みフラグ |

### 4. ClassificationResult

LLMによる分類結果。

| Field | Type | Description |
|-------|------|-------------|
| file | MarkdownFile | 対象ファイル |
| genre | string | 判定ジャンル（Vault名） |
| subfolder | string | 判定サブフォルダ名 |
| is_new_subfolder | bool | 新規フォルダ提案か |
| confidence | float | 確信度（0.0-1.0） |
| reason | string | 判定理由 |

### 5. MoveOperation

ファイル移動操作の記録。

| Field | Type | Description |
|-------|------|-------------|
| file | MarkdownFile | 対象ファイル |
| source_path | Path | 移動元パス |
| dest_path | Path | 移動先パス |
| status | enum | pending / executed / failed / skipped |
| error | string | エラーメッセージ（失敗時） |
| timestamp | datetime | 操作日時 |

### 6. MoveLog

移動操作のセッションログ。

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | セッション識別子（タイムスタンプ） |
| vault | string | 対象Vault名 |
| operations | list[MoveOperation] | 操作一覧 |
| stats | dict | 統計（成功/失敗/スキップ数） |
| created_at | datetime | ログ作成日時 |

## Relationships

```
Vault (1) ─────── (*) Subfolder
  │
  └──────────── (*) MarkdownFile
                      │
                      └── (1) ClassificationResult
                               │
                               └── (1) MoveOperation
                                        │
                                        └── (*:1) MoveLog
```

## State Transitions

### MoveOperation.status

```
pending ──┬── executed (移動成功)
          ├── failed (エラー発生)
          └── skipped (ユーザーがスキップ)
```

## Validation Rules

1. **MarkdownFile.normalized**: `true`のファイルのみ階層化対象
2. **ClassificationResult.confidence**: 0.5未満の場合は「未分類」フォルダへ
3. **Subfolder.name**: 既存フォルダ名と完全一致で再利用、なければ新規作成
4. **MoveOperation**: 同名ファイル存在時はサフィックス付与（_1, _2...）

## Storage Format

### 移動ログ（JSON）

```json
{
  "session_id": "20260115_143052",
  "vault": "エンジニア",
  "operations": [
    {
      "file": "Dockerの基本.md",
      "source": "エンジニア/Dockerの基本.md",
      "dest": "エンジニア/Docker/Dockerの基本.md",
      "status": "executed",
      "timestamp": "2026-01-15T14:30:55"
    }
  ],
  "stats": {
    "total": 50,
    "executed": 48,
    "failed": 1,
    "skipped": 1
  }
}
```

### 分類結果（CSV/JSON）

ドライランモードで出力される提案一覧。

```csv
ファイル名,現在位置,提案先,確信度,理由,新規フォルダ
Dockerの基本,エンジニア/,エンジニア/Docker/,0.92,Docker関連技術メモ,No
```
