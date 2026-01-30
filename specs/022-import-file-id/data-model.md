# Data Model: LLMインポートでのfile_id付与

**Date**: 2026-01-18
**Feature**: 022-import-file-id

## エンティティ定義

### KnowledgeDocument (変更)

抽出されたナレッジドキュメントを表すデータクラス。

```python
@dataclass
class KnowledgeDocument:
    """抽出されたナレッジドキュメント"""
    title: str
    summary: str
    created: str
    source_provider: str
    source_conversation: str
    summary_content: str
    key_learnings: list[str]
    code_snippets: list[CodeSnippet]
    normalized: bool = True
    file_id: str = ""  # 新規追加
```

| フィールド | 型 | 説明 | 変更 |
|------------|-----|------|------|
| `title` | str | ナレッジタイトル | - |
| `summary` | str | 1行要約（frontmatter用） | - |
| `created` | str | 作成日（YYYY-MM-DD） | - |
| `source_provider` | str | プロバイダー名（"claude"等） | - |
| `source_conversation` | str | 元の会話ID | - |
| `summary_content` | str | 構造化されたまとめ | - |
| `key_learnings` | list[str] | 主要な学び | - |
| `code_snippets` | list[CodeSnippet] | コードスニペット | - |
| `normalized` | bool | 正規化フラグ | - |
| **`file_id`** | **str** | **12文字16進数ハッシュID** | **新規** |

### ProcessedEntry (変更)

処理済みエントリを表すデータクラス。

```python
@dataclass
class ProcessedEntry:
    """処理済みエントリ"""
    id: str
    provider: str
    input_file: str
    output_file: str
    processed_at: str
    status: str  # "success" | "skipped" | "error"
    skip_reason: str | None = None
    error_message: str | None = None
    file_id: str | None = None  # 新規追加
```

| フィールド | 型 | 説明 | 変更 |
|------------|-----|------|------|
| `id` | str | 会話ID（プロバイダー固有） | - |
| `provider` | str | プロバイダー名 | - |
| `input_file` | str | Phase 1 出力ファイルパス | - |
| `output_file` | str | Phase 2 出力ファイルパス | - |
| `processed_at` | str | 処理日時（ISO 8601） | - |
| `status` | str | 処理ステータス | - |
| `skip_reason` | str \| None | スキップ理由 | - |
| `error_message` | str \| None | エラーメッセージ | - |
| **`file_id`** | **str \| None** | **ファイル追跡用ID** | **新規** |

## file_id 仕様

### 形式

- **長さ**: 12文字
- **文字種**: 16進数（0-9, a-f）
- **例**: `a1b2c3d4e5f6`

### 生成アルゴリズム

```python
def generate_file_id(content: str, filepath: Path) -> str:
    """
    ファイルコンテンツと初回パスからハッシュIDを生成

    Args:
        content: Markdownコンテンツ（frontmatter含む）
        filepath: 出力ファイルの相対パス

    Returns:
        12文字の16進数ハッシュID
    """
    path_str = filepath.as_posix()
    combined = f"{content}\n---\n{path_str}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]
```

### 特性

| 特性 | 説明 |
|------|------|
| **決定論的** | 同一コンテンツ + 同一パス → 同一 file_id |
| **一意性** | 48ビット（約281兆通り）で実用上衝突なし |
| **不変性** | コンテンツ変更 → file_id 変更（追跡可能） |

## frontmatter 出力形式

```yaml
---
title: ナレッジタイトル
summary: 1行要約
created: 2026-01-18
source_provider: claude
source_conversation: abc123
file_id: a1b2c3d4e5f6  # 新規追加
normalized: true
---
```

## state.json 出力形式

```json
{
  "processed_conversations": {
    "conversation-id-123": {
      "id": "conversation-id-123",
      "provider": "claude",
      "input_file": ".staging/@llm_exports/claude/parsed/conversations/xxx.md",
      "output_file": ".staging/@index/Knowledge_xxx.md",
      "processed_at": "2026-01-18T12:00:00",
      "status": "success",
      "file_id": "a1b2c3d4e5f6"
    }
  }
}
```

## バリデーションルール

| ルール | 説明 |
|--------|------|
| file_id 形式 | `/^[0-9a-f]{12}$/` にマッチすること |
| file_id 空許容 | KnowledgeDocument では空文字列を許容（生成前） |
| file_id None許容 | ProcessedEntry では None を許容（エラー時） |

## 状態遷移

```
[Phase 1 完了]
    ↓
[Phase 2 開始] → file_id 未設定 (empty string)
    ↓
[コンテンツ生成]
    ↓
[出力パス決定]
    ↓
[file_id 生成] → KnowledgeDocument.file_id = "a1b2c3d4e5f6"
    ↓
[ファイル書き込み]
    ↓
[state.json 更新] → ProcessedEntry.file_id = "a1b2c3d4e5f6"
```
