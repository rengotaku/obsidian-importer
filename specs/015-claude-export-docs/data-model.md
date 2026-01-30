# Data Model: Claude Export Knowledge Extraction

**Feature**: 015-claude-export-docs
**Date**: 2026-01-16

## Entities

### Base Classes (共通インターフェース)

新しいプロバイダー追加時に実装すべき基底クラス。

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class BaseConversation(ABC):
    """会話データの共通インターフェース"""
    id: str                      # 会話の一意識別子
    title: str                   # 会話タイトル
    created_at: str              # ISO 8601形式の作成日時
    messages: list['BaseMessage']

    @property
    @abstractmethod
    def provider(self) -> str:
        """プロバイダー名（'claude', 'chatgpt', etc.）"""
        pass

@dataclass
class BaseMessage(ABC):
    """メッセージの共通インターフェース"""
    role: str           # "user" | "assistant" | "system"
    content: str        # メッセージ本文
    timestamp: str      # ISO 8601形式

class BaseParser(ABC):
    """エクスポートパーサーの共通インターフェース"""

    @abstractmethod
    def parse(self, export_path: Path) -> list[BaseConversation]:
        """エクスポートデータをパースして会話リストを返す"""
        pass

    @abstractmethod
    def to_markdown(self, conversation: BaseConversation) -> str:
        """会話をMarkdown形式に変換"""
        pass
```

### Claude Provider (Claude固有)

```python
@dataclass
class ClaudeConversation(BaseConversation):
    """Claude エクスポートの会話データ"""
    uuid: str                    # Claude固有のUUID
    summary: str | None          # Claude生成のサマリー（英語）
    updated_at: str              # 更新日時

    @property
    def provider(self) -> str:
        return "claude"

    @property
    def id(self) -> str:
        return self.uuid

@dataclass
class ClaudeMessage(BaseMessage):
    """Claude会話内のメッセージ"""
    uuid: str           # メッセージID
    sender: str         # "human" | "assistant"
    attachments: list   # 添付ファイル（未処理）

    @property
    def role(self) -> str:
        return "user" if self.sender == "human" else "assistant"
```

### ChatGPT Provider (将来実装)

```python
@dataclass
class ChatGPTConversation(BaseConversation):
    """ChatGPT エクスポートの会話データ"""
    conversation_id: str
    model: str | None            # 使用モデル（gpt-4等）

    @property
    def provider(self) -> str:
        return "chatgpt"

@dataclass
class ChatGPTMessage(BaseMessage):
    """ChatGPT会話内のメッセージ"""
    author_role: str    # "user" | "assistant" | "system"
    model_slug: str | None
```

### KnowledgeDocument (Output)

会話から抽出された知識を含む構造化ドキュメント（プロバイダー共通）。

```python
@dataclass
class KnowledgeDocument:
    """抽出されたナレッジドキュメント"""
    # Frontmatter
    title: str                          # 会話から抽出したタイトル
    tags: list[str]                     # 抽出されたタグ（3-5個）
    created: str                        # YYYY-MM-DD形式の作成日
    source_provider: str                # プロバイダー名（"claude", "chatgpt"）★
    source_conversation: str            # 元の会話ID
    normalized: bool = False            # 正規化フラグ（Phase 3で処理）

    # Content sections
    overview: str                       # 概要（1-2段落）
    key_learnings: list[str]            # 主要な学び（3-5項目）
    action_items: list[str]             # 実践的なアクション（チェックボックス形式）
    code_snippets: list[CodeSnippet]    # コードスニペット（あれば）
    related_links: list[str]            # 関連リンク（[[]] 形式）
```

### CodeSnippet (Output)

抽出されたコードスニペット。

```python
@dataclass
class CodeSnippet:
    """抽出されたコードスニペット"""
    language: str       # プログラミング言語
    code: str           # コード本文
    description: str    # 説明（オプション）
```

### ExtractionResult (Internal)

LLM からの抽出結果を表す内部データ構造。

```python
@dataclass
class ExtractionResult:
    """LLMからの抽出結果"""
    success: bool
    data: KnowledgeData | None
    error: str | None
    raw_response: str | None
    retry_count: int
```

### KnowledgeData (Internal)

LLM の JSON 出力をパースした中間データ。

```python
@dataclass
class KnowledgeData:
    """LLM出力の中間データ"""
    title: str
    overview: str
    key_learnings: list[str]
    action_items: list[str]
    code_snippets: list[dict]  # {"language": str, "code": str, "description": str}
    tags: list[str]
    related_keywords: list[str]
```

### ProcessingState (Persistence)

処理状態を追跡する JSON ファイルの構造（プロバイダーごとに独立）。

```python
@dataclass
class ProcessingState:
    """処理状態"""
    provider: str                                       # プロバイダー名 ★
    processed_conversations: dict[str, ProcessedEntry]  # ID -> エントリ
    last_run: str                                       # ISO 8601形式
    version: str = "1.0"                                # 状態ファイルバージョン

@dataclass
class ProcessedEntry:
    """処理済みエントリ"""
    id: str                     # 会話ID（プロバイダー固有）
    provider: str               # プロバイダー名 ★
    input_file: str             # Phase 1出力ファイルパス
    output_file: str            # Phase 2出力ファイルパス
    processed_at: str           # 処理日時
    status: str                 # "success" | "skipped" | "error"
    skip_reason: str | None     # スキップ理由（status=skippedの場合）
    error_message: str | None   # エラーメッセージ（status=errorの場合）
```

**状態ファイルの配置**:
- Claude: `@index/llm_exports/claude/.extraction_state.json`
- ChatGPT: `@index/llm_exports/chatgpt/.extraction_state.json`

## Relationships

```
                    ┌─────────────────────────────────────┐
                    │         LLM Export Data             │
                    │  (conversations.json / export.json) │
                    └─────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │   ClaudeParser    │           │  ChatGPTParser    │
        │   (provider)      │           │  (provider)       │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │ClaudeConversation │           │ChatGPTConversation│
        │ extends Base      │           │ extends Base      │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │   KnowledgeExtractor (共通)   │
                    │   - source_provider 付与      │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      KnowledgeDocument        │
                    │   - source_provider: str      │
                    │   - source_conversation: str  │
                    │   - normalized: false         │
                    └───────────────────────────────┘
                                    │
                                    ▼ Phase 3
                    ┌───────────────────────────────┐
                    │        Vault Document         │
                    │      (normalized: true)       │
                    └───────────────────────────────┘
```

## Validation Rules

### Conversation Validation
- `uuid`: 非空文字列、UUID形式
- `chat_messages`: 配列（空の場合はスキップ候補）

### KnowledgeDocument Validation
- `title`: 1-200文字、ファイルシステム禁止文字なし
- `tags`: 1-5個、各タグは1-50文字
- `created`: YYYY-MM-DD形式
- `overview`: 1-1000文字
- `key_learnings`: 1-10項目、各50-500文字
- `action_items`: 0-10項目、各10-200文字

### Skip Criteria
| 条件 | 判定 |
|------|------|
| メッセージ数 ≤ 2 | スキップ候補 |
| 総文字数 ≤ 500 | スキップ候補 |
| 全メッセージが空 | スキップ |

## State Transitions

```
Input File State:
  @index/claude/parsed/conversations/*.md
      │
      ▼ [処理開始]
  Processing
      │
      ├─ [成功] ──▶ Deleted (中間ファイル削除)
      │              └── Output: @index/*.md
      │
      ├─ [スキップ] ──▶ Deleted (短い会話)
      │              └── Output: @index/*.md (簡略版)
      │
      └─ [エラー] ──▶ Retained (再処理用に保持)
                    └── Error logged in state.json
```

## File Naming Convention

### Input (Phase 1 Output)
```
{YYYY-MM-DD}_{sanitized_title}.md
例: 2025-12-15_Claude_Code_Setup.md
```

### Output (Phase 2 Output)
```
{sanitized_title}.md
例: Claude Code セットアップガイド.md
```

**Sanitization Rules**:
- ファイルシステム禁止文字 (`<>:"/\|?*`) → `_`
- 連続アンダースコア → 単一に
- 先頭/末尾の空白・アンダースコア → 除去
- 最大80文字
