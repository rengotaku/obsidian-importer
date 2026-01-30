"""
llm_import.providers.claude.parser - Claude エクスポートパーサー

Claude (web) エクスポートデータ（conversations.json）をパースし、
Markdown 形式の会話ログを生成する。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from scripts.llm_import.base import BaseMessage, BaseConversation, BaseParser


# =============================================================================
# Claude Data Classes
# =============================================================================


@dataclass
class ClaudeMessage(BaseMessage):
    """
    Claude 会話内のメッセージ

    Attributes:
        uuid: メッセージID
        content: メッセージ本文
        timestamp: ISO 8601 形式のタイムスタンプ
        sender: "human" | "assistant"
    """
    uuid: str
    sender: str  # "human" | "assistant"

    @property
    def role(self) -> str:
        """
        メッセージの役割を返す

        Returns:
            "user" | "assistant"
        """
        return "user" if self.sender == "human" else "assistant"


@dataclass
class ClaudeConversation(BaseConversation):
    """
    Claude エクスポートの会話データ

    Attributes:
        uuid: Claude 固有の UUID
        title: 会話タイトル
        created_at: 作成日時
        updated_at: 更新日時
        summary: Claude 生成のサマリー（英語、None の場合あり）
        _messages: メッセージのリスト
    """
    uuid: str
    updated_at: str
    summary: str | None = None
    _messages: list[ClaudeMessage] = field(default_factory=list)

    @property
    def messages(self) -> list[ClaudeMessage]:
        """メッセージのリストを返す"""
        return self._messages

    @property
    def id(self) -> str:
        """会話の一意識別子を返す"""
        return self.uuid

    @property
    def provider(self) -> str:
        """プロバイダー名を返す"""
        return "claude"


# =============================================================================
# Claude Parser
# =============================================================================


class ClaudeParser(BaseParser):
    """
    Claude エクスポートパーサー

    conversations.json をパースして ClaudeConversation のリストを生成する。
    """

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        return "claude"

    def parse(self, export_path: Path) -> list[ClaudeConversation]:
        """
        エクスポートデータをパースして会話リストを返す

        Args:
            export_path: conversations.json のパスまたはディレクトリ

        Returns:
            会話のリスト
        """
        # ディレクトリの場合は conversations.json を探す
        if export_path.is_dir():
            json_path = export_path / "conversations.json"
            if not json_path.exists():
                # サブディレクトリを探す
                for subdir in export_path.iterdir():
                    if subdir.is_dir():
                        candidate = subdir / "conversations.json"
                        if candidate.exists():
                            json_path = candidate
                            break
        else:
            json_path = export_path

        if not json_path.exists():
            raise FileNotFoundError(f"conversations.json が見つかりません: {export_path}")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        conversations = []
        for conv_data in data:
            conv = self._parse_conversation(conv_data)
            conversations.append(conv)

        return conversations

    def _parse_conversation(self, data: dict) -> ClaudeConversation:
        """
        会話データをパース

        Args:
            data: 会話の JSON データ

        Returns:
            ClaudeConversation
        """
        messages = []
        for msg_data in data.get("chat_messages", []):
            msg = self._parse_message(msg_data)
            messages.append(msg)

        return ClaudeConversation(
            uuid=data.get("uuid", ""),
            title=data.get("name", "Untitled"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            summary=data.get("summary"),
            _messages=messages,
        )

    def _parse_message(self, data: dict) -> ClaudeMessage:
        """
        メッセージデータをパース

        Args:
            data: メッセージの JSON データ

        Returns:
            ClaudeMessage
        """
        # content 配列から text を抽出（複数ある場合は結合）
        content_parts = []
        for content_item in data.get("content", []):
            if content_item.get("type") == "text":
                text = content_item.get("text", "")
                if text:
                    content_parts.append(text)

        # content 配列が空の場合は text フィールドを使用
        content = "\n".join(content_parts) if content_parts else data.get("text", "")

        return ClaudeMessage(
            uuid=data.get("uuid", ""),
            content=content,
            timestamp=data.get("created_at", ""),
            sender=data.get("sender", "human"),
        )

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
        lines.append(f"created: {self._format_date(conversation.created_at)}")
        lines.append(f"updated: {self._format_date(conversation.updated_at)}")
        lines.append("tags:")
        lines.append("  - claude-export")
        lines.append("---")
        lines.append("")

        # サマリー（あれば）
        if conversation.summary:
            lines.append("## Summary")
            lines.append("")
            lines.append(conversation.summary)
            lines.append("")

        # 会話
        lines.append("## 会話")
        lines.append("")

        for msg in conversation.messages:
            role_label = "**User**" if msg.role == "user" else "**Assistant**"
            lines.append(f"{role_label}:")
            lines.append("")
            lines.append(msg.content.strip())
            lines.append("")

        return "\n".join(lines)

    def _format_date(self, iso_timestamp: str) -> str:
        """
        ISO タイムスタンプを YYYY-MM-DD 形式に変換

        Args:
            iso_timestamp: ISO 8601 形式のタイムスタンプ

        Returns:
            YYYY-MM-DD 形式の日付文字列
        """
        if not iso_timestamp:
            return ""
        # 2025-12-20T09:28:24.439525Z → 2025-12-20
        return iso_timestamp[:10]
