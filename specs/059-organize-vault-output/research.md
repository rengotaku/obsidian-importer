# Research: Organize パイプラインの Obsidian Vault 直接出力対応

**Date**: 2026-02-20
**Branch**: 059-organize-vault-output

## 1. パイプライン設計

### Decision: 独立パイプラインとして実装

**Rationale**:
- FR-009 で `__default__` に含めない要件が明確
- Vault へのコピーは破壊的操作のため、明示的な実行が必要
- Preview → 実行 の 2 段階ワークフローを推奨

**Alternatives considered**:
- ❌ 既存 organize パイプラインの拡張: 関心事の分離が不明確になる
- ❌ CLI スクリプト: Kedro パイプラインの統一性が失われる

### Implementation

```python
# pipeline_registry.py に追加
pipelines["organize_preview"] = vault_output.create_preview_pipeline()
pipelines["organize_to_vault"] = vault_output.create_vault_pipeline()
# __default__ には含めない
```

## 2. Vault マッピング設計

### Decision: parameters.yml で設定可能なマッピング

**Rationale**:
- Issue#24 で定義されたマッピングをそのまま採用
- 設定ファイルで変更可能にすることで柔軟性を確保

**Mapping**:

| Genre | Vault |
|-------|-------|
| ai, devops, engineer | エンジニア |
| business | ビジネス |
| economy | 経済 |
| health, parenting, travel, lifestyle, daily | 日常 |
| other | その他 |

**Alternatives considered**:
- ❌ ハードコード: 変更が困難
- ❌ 外部 JSON ファイル: 設定の分散

## 3. 競合処理設計

### Decision: 3 つのモード（skip/overwrite/increment）

**Rationale**:
- Issue#24 の要件に準拠
- デフォルト `skip` で安全性を確保

**Implementation**:

```python
def handle_conflict(src: Path, dst: Path, mode: str) -> Path | None:
    """競合処理

    Args:
        src: ソースファイル
        dst: 出力先パス
        mode: skip | overwrite | increment

    Returns:
        実際の出力先パス（skip の場合は None）
    """
    if not dst.exists():
        return dst

    if mode == "skip":
        return None
    elif mode == "overwrite":
        return dst
    elif mode == "increment":
        return find_incremented_path(dst)  # file_1.md, file_2.md, ...
```

## 4. フォルダ構造設計

### Decision: topic をサブフォルダとして使用

**Rationale**:
- Issue#24 の要件: genre はフォルダを作成しない（Vault マッピングのみ）
- topic が空の場合は Vault 直下に配置

**Structure**:

```
/home/takuya/Documents/Obsidian/Vaults/
├── エンジニア/
│   ├── python/
│   │   └── file1.md
│   └── file2.md         # topic が空の場合
├── ビジネス/
│   └── marketing/
│       └── file3.md
└── ...
```

**Edge Cases**:
- topic に `/` や `\` が含まれる場合は `_` に正規化
- topic が空文字の場合は Vault 直下

## 5. Preview モード設計

### Decision: ログ出力 + 戻り値で情報提供

**Rationale**:
- Kedro パイプラインの標準的なパターン
- 実際のファイル操作は行わない（dry-run）

**Output Format**:

```
Preview: Vault Output Summary
=============================
Total files: 50
Destination breakdown:
  エンジニア: 25 files
  ビジネス: 10 files
  日常: 12 files
  その他: 3 files

Conflicts detected: 3
  - /path/to/vault/file1.md (existing)
  - /path/to/vault/file2.md (existing)
  ...
```

## 6. ソースファイル読み込み

### Decision: PartitionedDataset から直接読み込み

**Rationale**:
- 既存の organize パイプラインの出力 (`organized_output`) を入力として使用
- 既に frontmatter に genre, topic が埋め込まれている

**Input Flow**:

```
data/07_model_output/organized/*.md (PartitionedDataset)
    ↓
read_organized_files node
    ↓
resolve_vault_destination node
    ↓
check_conflicts node (preview のみ)
    ↓
copy_to_vault node (実行のみ)
```

## 7. エラーハンドリング

### Decision: 部分成功を許容

**Rationale**:
- 1 ファイルの失敗で全体を停止しない
- エラーログで詳細を記録

**Error Cases**:
- Vault ベースパスが存在しない → エラーで中断
- 権限エラー → ファイルをスキップしてログ
- frontmatter パースエラー → ファイルをスキップしてログ

## 8. テスト戦略

### Decision: 単体テスト + 統合テスト

**Unit Tests**:
- `resolve_vault_destination`: genre → Vault マッピング
- `handle_conflict`: 競合処理ロジック
- `sanitize_topic`: topic の正規化

**Integration Tests**:
- 一時ディレクトリでの実際のファイルコピー
- Preview モードの出力検証

## Summary

| 項目 | 決定 |
|------|------|
| パイプライン | `organize_preview`, `organize_to_vault` を独立登録 |
| マッピング | parameters.yml で設定 |
| 競合処理 | skip (default), overwrite, increment |
| フォルダ | Vault/{topic}/file.md |
| エラー | 部分成功を許容 |
