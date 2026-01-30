# Research: LLMインポートでのfile_id付与

**Date**: 2026-01-18
**Feature**: 022-import-file-id

## 調査サマリ

本機能は明確な要件と既存実装があるため、NEEDS CLARIFICATION は発生しなかった。以下は主要な技術決定の記録。

## 決定事項

### 1. file_id 生成ロジックの配置

**Decision**: `llm_import/common/file_id.py` に新規モジュールとして配置

**Rationale**:
- normalizer の `generate_file_id()` と同一アルゴリズムを使用
- 将来的に normalizer から import 可能（コード重複回避）
- llm_import 内で完結させることで依存関係をシンプルに保つ

**Alternatives Considered**:
1. normalizer から直接 import → 循環依存のリスク、パス問題
2. 共通ライブラリに抽出 → 過剰な抽象化、現時点では不要

### 2. file_id の生成タイミング

**Decision**: Phase 2 出力時（`cli.py` で KnowledgeDocument 生成後、ファイル書き込み前）

**Rationale**:
- 出力パスが確定してから生成する必要がある（ハッシュ入力に含むため）
- チャンク分割後に各チャンクの出力パスが決まる
- エラー発生前に file_id を生成するため、エラー追跡にも使用可能

**Alternatives Considered**:
1. Phase 1 時点で生成 → 出力パスが未確定のため不可
2. ファイル書き込み後に生成 → 状態管理との整合性が取れない

### 3. ProcessedEntry への file_id 追加方法

**Decision**: Optional フィールドとして追加（`file_id: str | None = None`）

**Rationale**:
- 後方互換性を維持（既存の state.json を破壊しない）
- エラー発生時は file_id が None の可能性がある
- `from_dict()` で欠損キーを許容

**Alternatives Considered**:
1. 必須フィールド → 既存データとの互換性問題
2. 別テーブル/ファイル → 過剰な複雑化

### 4. KnowledgeDocument への file_id 追加方法

**Decision**: dataclass フィールドとして追加（`file_id: str = ""`）

**Rationale**:
- `to_markdown()` で frontmatter に出力
- 空文字列をデフォルトとし、生成前は空を許容
- チャンク分割時は各チャンクに異なる file_id を設定

**Alternatives Considered**:
1. None デフォルト → frontmatter 出力時の条件分岐が増える
2. 必須引数 → 既存のインスタンス生成コードへの影響大

## 既存コード分析

### generate_file_id() (normalizer/processing/single.py)

```python
def generate_file_id(content: str, filepath: Path) -> str:
    """ファイルコンテンツと初回パスからハッシュIDを生成"""
    path_str = filepath.as_posix()
    combined = f"{content}\n---\n{path_str}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]
```

- 12文字の16進数（SHA-256の先頭48ビット）
- コンテンツ + パスを結合してハッシュ化
- 決定論的（同一入力→同一出力）

### 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `common/file_id.py` | 新規作成: generate_file_id() |
| `common/knowledge_extractor.py` | KnowledgeDocument に file_id 追加、to_markdown() 修正 |
| `common/state.py` | ProcessedEntry に file_id 追加 |
| `cli.py` | file_id 生成・設定ロジック追加 |
| `tests/test_file_id.py` | 新規作成: file_id生成テスト |
| `tests/test_knowledge_extractor.py` | file_id 関連テスト追加 |

## リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 既存 state.json との互換性 | 低 | Optional フィールド採用で回避 |
| チャンク分割時の file_id 重複 | 低 | 各チャンクに異なる出力パス → 異なる file_id |
| ハッシュ衝突 | 極低 | 12文字（48ビット）で実用上問題なし |
