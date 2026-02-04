# Phase 2 完了: User Story 1 - Phase 1 完了時点でのファイル追跡

## 概要

Phase 2 では、Phase 1（パース）完了時点で parsed ファイルの frontmatter に `file_id` を含める機能を実装した。

## 実行タスク

| タスク | 説明 | 結果 |
|--------|------|------|
| T005 | 前フェーズ出力読み込み | 完了 |
| T006 | `ClaudeParser.to_markdown()` に `file_id` パラメータ追加 | 完了 |
| T007 | `to_markdown()` with file_id のテスト追加 | 完了 |
| T008 | `cli.py` Phase 1 処理で file_id を生成・パス | 完了 |
| T009 | Phase 1 file_id 生成のテスト追加 | 完了 |
| T010 | `make test` で全テストパス確認 | 完了 |
| T011 | Phase 2 出力生成 | 本ファイル |

## 実装内容

### T006: `ClaudeParser.to_markdown()` の変更

**ファイル**: `development/scripts/llm_import/providers/claude/parser.py`

```python
def to_markdown(
    self,
    conversation: ClaudeConversation,
    file_id: str | None = None,
) -> str:
    """
    会話を Markdown 形式に変換

    Args:
        conversation: 変換する会話データ
        file_id: ファイル追跡用ID（12文字の16進数ハッシュ）

    Returns:
        Markdown 形式の文字列
    """
    lines = []

    # Frontmatter
    lines.append("---")
    lines.append(f"title: {conversation.title}")
    lines.append(f"uuid: {conversation.uuid}")
    if file_id:
        lines.append(f"file_id: {file_id}")
    # ... 以下省略
```

**変更点**:
- `file_id: str | None = None` パラメータを追加（オプショナル）
- `file_id` が指定された場合、frontmatter の `uuid` の直後に出力
- 後方互換性を維持（`file_id` なしでも動作）

### T008: `cli.py` Phase 1 処理の変更

**ファイル**: `development/scripts/llm_import/cli.py`

```python
# Phase 1: JSON → Markdown (T024)
if not phase2_only:
    phase1_start = time.time()
    phase1_filename = _generate_filename(conv) + ".md"
    phase1_path = parsed_dir / phase1_filename

    # T008: Phase 1 で file_id を生成（コンテンツ + パスから計算）
    # 一度 file_id なしで markdown 生成 → file_id 計算 → 再生成
    markdown_without_id = parser.to_markdown(conv)
    relative_path = phase1_path.relative_to(parsed_dir.parent.parent)
    phase1_file_id = generate_file_id(markdown_without_id, relative_path)
    markdown = parser.to_markdown(conv, file_id=phase1_file_id)

    phase1_path.write_text(markdown, encoding="utf-8")
    phase1_ok = True
```

**変更点**:
- `generate_file_id()` を使用して file_id を生成
- コンテンツ（file_id なし）と相対パスから決定論的にハッシュを計算
- 生成した file_id を `to_markdown()` に渡して frontmatter に含める

### T007, T009: テストの追加

**ファイル**: `development/scripts/llm_import/tests/providers/test_claude_parser.py`

追加テスト:
- `test_to_markdown_with_file_id`: file_id が frontmatter に含まれることを確認
- `test_to_markdown_without_file_id`: file_id なしの場合に含まれないことを確認
- `test_to_markdown_file_id_none_explicitly`: `file_id=None` でも含まれないことを確認

**ファイル**: `development/scripts/llm_import/tests/test_cli.py`

追加テストクラス `TestPhase1FileIdGeneration`:
- `test_phase1_generates_file_id_in_frontmatter`: Phase 1 処理が file_id を生成すること
- `test_phase1_file_id_is_deterministic`: 同じ入力で同じ file_id が生成されること
- `test_phase1_different_content_different_file_id`: 異なる内容で異なる file_id が生成されること

## テスト結果

```
Ran 238 tests in 0.149s
OK (skipped=1)
```

- normalizer テスト: 123件 OK
- 統合テスト: 6件 OK
- llm_import テスト: 109件 OK（+3件追加）

## 出力例

Phase 1 処理後の parsed ファイル:

```yaml
---
title: 卓上IHでピザを保温する方法
uuid: 154457f7-2ec2-4c8d-9751-0bbfe6d64fa9
file_id: a1b2c3d4e5f6
created: 2025-12-20
updated: 2025-12-20
tags:
  - claude-export
---
```

## 次フェーズへの引き継ぎ

### 利用可能な機能

1. **`ClaudeParser.to_markdown(conv, file_id=...)`** - file_id 付きの Markdown 生成
2. **Phase 1 での file_id 自動生成** - `cli.py` で parsed ファイルに file_id が含まれる

### Phase 3 での作業

1. `session_logger.log_stage()` に `file_id` パラメータを追加
2. `pipeline_stages.jsonl` に file_id を記録
3. Phase 2 での file_id 継承

## Checkpoint 確認

Phase 1 parsed ファイルに file_id が含まれる:
- `ClaudeParser.to_markdown()` が `file_id` パラメータをサポート
- `cli.py` Phase 1 処理で `generate_file_id()` を使用して file_id を生成
- frontmatter に `file_id: [12文字16進数]` が出力される
