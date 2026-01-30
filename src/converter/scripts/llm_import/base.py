"""
llm_import.base - 共通インターフェースと基底クラス

新しいプロバイダー追加時に実装すべき基底クラスを定義。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# Base Classes for Messages and Conversations
# =============================================================================


@dataclass
class BaseMessage(ABC):
    """
    メッセージの共通インターフェース

    Attributes:
        content: メッセージ本文
        timestamp: ISO 8601 形式のタイムスタンプ
    """
    content: str
    timestamp: str

    @property
    @abstractmethod
    def role(self) -> str:
        """
        メッセージの役割を返す

        Returns:
            "user" | "assistant" | "system"
        """
        pass


@dataclass
class BaseConversation(ABC):
    """
    会話データの共通インターフェース

    Attributes:
        title: 会話タイトル
        created_at: ISO 8601 形式の作成日時
    """
    title: str
    created_at: str

    # messagesは具象クラスで定義（dataclass継承の順序問題を回避）
    @property
    @abstractmethod
    def messages(self) -> list[BaseMessage]:
        """メッセージのリストを返す"""
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """会話の一意識別子を返す"""
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        """プロバイダー名を返す（例: 'claude', 'chatgpt'）"""
        pass


# =============================================================================
# Base Parser Class
# =============================================================================


class BaseParser(ABC):
    """
    エクスポートパーサーの共通インターフェース

    新しいプロバイダーを追加する際はこのクラスを継承し、
    parse() と to_markdown() を実装する。
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        プロバイダー名を返す

        Returns:
            プロバイダー名（例: 'claude', 'chatgpt'）
        """
        pass

    @abstractmethod
    def parse(self, export_path: Path) -> list[BaseConversation]:
        """
        エクスポートデータをパースして会話リストを返す

        Args:
            export_path: エクスポートデータのパス（ディレクトリまたはファイル）

        Returns:
            会話のリスト
        """
        pass

    @abstractmethod
    def to_markdown(self, conversation: BaseConversation) -> str:
        """
        会話を Markdown 形式に変換

        Args:
            conversation: 変換する会話データ

        Returns:
            Markdown 形式の文字列
        """
        pass

    def get_output_dir(self, base_dir: Path) -> Path:
        """
        Phase 1 出力ディレクトリを取得

        Args:
            base_dir: ベースディレクトリ（例: @index/llm_exports/）

        Returns:
            出力ディレクトリのパス
        """
        return base_dir / self.provider_name / "parsed" / "conversations"


# =============================================================================
# Utility Functions
# =============================================================================


def sanitize_filename(title: str, max_length: int = 80) -> str:
    """
    ファイル名として安全な文字列に変換

    Args:
        title: 元のタイトル
        max_length: 最大文字数（デフォルト: 80）

    Returns:
        サニタイズされたファイル名
    """
    # ファイルシステム禁止文字を置換
    forbidden_chars = '<>:"/\\|?*'
    result = title
    for char in forbidden_chars:
        result = result.replace(char, '_')

    # 連続アンダースコアを単一に
    while '__' in result:
        result = result.replace('__', '_')

    # 先頭/末尾の空白・アンダースコアを除去
    result = result.strip(' _')

    # 最大長で切り詰め
    if len(result) > max_length:
        result = result[:max_length].rstrip(' _')

    return result or "untitled"
