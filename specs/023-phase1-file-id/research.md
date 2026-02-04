# Research: 全工程での file_id 付与・維持

**Feature**: 023-phase1-file-id
**Date**: 2026-01-18

## 調査サマリー

既存コードベースを調査し、file_id 関連の実装状況を確認した。

## 1. file_id 生成ロジック

### 既存実装

**`development/scripts/llm_import/common/file_id.py`**:
```python
def generate_file_id(content: str, filepath: Path) -> str:
    path_str = filepath.as_posix()
    combined = f"{content}\n---\n{path_str}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]
```

**`development/scripts/normalizer/processing/single.py`**:
- 同一アルゴリズムの `generate_file_id()` が実装済み
- `build_normalized_file()` は `file_id` パラメータを受け取り、frontmatter に出力可能

### 決定事項

- **Decision**: 既存の `generate_file_id()` をそのまま再利用
- **Rationale**: SHA-256 先頭12文字は衝突確率が十分低く（2^48 ≈ 281兆）、決定論的
- **Alternatives**: UUID（却下: 決定論性がない）、SHA-1（却下: 非推奨）

---

## 2. Phase 1（LLM Import パース）

### 現状

**`development/scripts/llm_import/providers/claude/parser.py`** の `to_markdown()`:
```python
def to_markdown(self, conversation: ClaudeConversation) -> str:
    lines = []
    lines.append("---")
    lines.append(f"title: {conversation.title}")
    lines.append(f"uuid: {conversation.uuid}")
    lines.append(f"created: {self._format_date(conversation.created_at)}")
    lines.append(f"updated: {self._format_date(conversation.updated_at)}")
    lines.append("tags:")
    lines.append("  - claude-export")
    lines.append("---")
    # ... (file_id なし)
```

### 必要な変更

1. `to_markdown()` に `file_id` パラメータを追加
2. frontmatter に `file_id: {value}` を出力
3. `cli.py` で file_id を生成し、`to_markdown()` に渡す

### 決定事項

- **Decision**: `ClaudeParser.to_markdown()` を拡張して file_id を受け取る
- **Rationale**: パーサー自体は file_id 生成責務を持たない（SRP）、cli.py で生成
- **Alternatives**: パーサー内で生成（却下: テスタビリティ低下）

---

## 3. pipeline_stages.jsonl

### 現状

**`development/scripts/llm_import/common/session_logger.py`** の `log_stage()`:
```python
def log_stage(self, filename, stage, timing_ms, executed=True, skipped_reason=None, ...):
    record = {
        "timestamp": timestamp(),
        "filename": filename,
        "stage": stage,
        "executed": executed,
        "timing_ms": timing_ms,
        "skipped_reason": skipped_reason,
    }
    # file_id フィールドなし
```

### 必要な変更

1. `log_stage()` に `file_id` パラメータを追加
2. `record` に `"file_id": file_id` を追加

### 決定事項

- **Decision**: `log_stage()` に optional `file_id` パラメータを追加
- **Rationale**: 後方互換性維持（既存呼び出しに影響なし）
- **Alternatives**: 新メソッド追加（却下: 冗長）

---

## 4. Normalizer（organize）

### 現状

**`development/scripts/normalizer/processing/single.py`**:
```python
# process_single_file() 内
result["file_id"] = generate_file_id(original_content, filepath)

# build_normalized_file() 呼び出し
normalized_content = build_normalized_file(
    norm_result,
    file_id=result["file_id"]  # 常に新規生成した file_id を使用
)
```

**問題点**: 既存の file_id があっても無視し、常に新規生成している。

### 必要な変更

1. `extract_frontmatter()` の結果から既存の `file_id` を取得
2. 既存 file_id があれば維持、なければ新規生成

### 決定事項

- **Decision**: `process_single_file()` で既存 file_id を確認し、維持優先
- **Rationale**: 「なければ生成、あれば維持」の原則に従う
- **Alternatives**: 常に上書き（却下: spec 要件違反）

---

## 5. Phase 2（ナレッジ抽出）

### 現状

**`development/scripts/llm_import/cli.py`**:
- Phase 2 で file_id を生成し、`KnowledgeDocument.file_id` に設定
- `to_markdown()` で frontmatter に出力

### 必要な変更

1. Phase 2 で parsed ファイルから file_id を読み取る
2. あれば継承、なければ新規生成

### 決定事項

- **Decision**: Phase 2 は parsed ファイルの file_id を継承優先
- **Rationale**: Phase 1 → Phase 2 のトレーサビリティ確保
- **Alternatives**: Phase 2 で常に再生成（却下: Phase 1 との file_id 不一致）

---

## 実装優先順位

| # | 変更箇所 | 影響範囲 | リスク |
|---|----------|----------|--------|
| 1 | `claude/parser.py` の `to_markdown()` | Phase 1 出力 | 低 |
| 2 | `session_logger.py` の `log_stage()` | JSONL ログ | 低 |
| 3 | `cli.py` Phase 1 処理 | file_id 生成・設定 | 中 |
| 4 | `cli.py` Phase 2 処理 | file_id 継承 | 中 |
| 5 | `normalizer/single.py` | organize 時の維持/生成 | 中 |

---

## テスト戦略

### ユニットテスト

1. `test_claude_parser.py`: `to_markdown()` の file_id 出力
2. `test_session_logger.py`: `log_stage()` の file_id 記録
3. `test_cli.py`: Phase 1 での file_id 生成、Phase 2 での継承
4. `test_file_id.py` (normalizer): 既存 file_id 維持

### 統合テスト

1. `make llm-import --phase1-only LIMIT=1` → parsed に file_id あり
2. `make llm-import LIMIT=1` → Phase 1 と Phase 2 で file_id 一致
3. `/og:organize` → file_id なしファイルに file_id 付与、あれば維持
