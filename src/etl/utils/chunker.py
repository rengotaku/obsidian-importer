"""
src.etl.utils.chunker - 会話チャンク分割モジュール

大規模会話をメッセージ境界で分割し、オーバーラップ付きチャンクを生成。

src/converter/scripts/llm_import/common/chunker.py からコピー。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# Protocol Definitions (replacing ABC imports from llm_import)
# =============================================================================


class MessageProtocol(Protocol):
    """メッセージのプロトコル定義"""
    content: str

    @property
    def role(self) -> str:
        """メッセージの役割を返す"""
        ...


class ConversationProtocol(Protocol):
    """会話のプロトコル定義"""
    title: str
    created_at: str

    @property
    def messages(self) -> list:
        """メッセージのリストを返す"""
        ...

    @property
    def id(self) -> str:
        """会話の一意識別子を返す"""
        ...

    @property
    def provider(self) -> str:
        """プロバイダー名を返す"""
        ...


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Chunk:
    """チャンク（分割された会話の一部）"""
    index: int                    # チャンク番号（0-indexed）
    messages: list                # このチャンクに含まれるメッセージ (list[MessageProtocol])
    char_count: int              # 文字数
    has_overlap: bool            # 前チャンクからのオーバーラップを含むか
    overlap_count: int           # オーバーラップメッセージ数


@dataclass
class ChunkResult:
    """チャンク処理結果"""
    chunk_index: int              # 処理したチャンク番号
    success: bool                 # 成功/失敗
    summary: str | None = None    # サマリー（成功時）
    learnings: list[str] = field(default_factory=list)  # 学び（成功時）
    code_snippets: list = field(default_factory=list)   # コードスニペット（成功時）
    error: str | None = None      # エラーメッセージ（失敗時）
    raw_response: str | None = None  # LLM 生レスポンス


@dataclass
class ChunkedConversation:
    """チャンク分割された会話"""
    original: object              # 元の会話 (ConversationProtocol)
    chunks: list[Chunk]           # チャンクリスト
    total_chars: int              # 元の総文字数
    chunk_size: int               # 使用したチャンクサイズ閾値


# =============================================================================
# Chunker Class
# =============================================================================


class Chunker:
    """
    会話をチャンクに分割するユーティリティクラス。

    メッセージ境界で分割し、文脈維持のためオーバーラップを設ける。
    """

    def __init__(
        self,
        chunk_size: int = 25000,
        overlap_messages: int = 2,
    ) -> None:
        """
        Args:
            chunk_size: チャンクサイズ閾値（文字数）
            overlap_messages: オーバーラップするメッセージ数
        """
        self.chunk_size = chunk_size
        self.overlap_messages = overlap_messages

    def should_chunk(self, conversation: ConversationProtocol) -> bool:
        """
        チャンク分割が必要か判定。

        Args:
            conversation: 会話データ

        Returns:
            True: 総文字数 >= chunk_size
            False: チャンク分割不要
        """
        total_chars = sum(len(m.content) for m in conversation.messages)
        return total_chars >= self.chunk_size

    def split(self, conversation: ConversationProtocol) -> ChunkedConversation:
        """
        会話をチャンクに分割。

        Args:
            conversation: 元の会話データ

        Returns:
            ChunkedConversation: 分割結果

        Raises:
            ValueError: 会話が空の場合
        """
        messages = conversation.messages
        if not messages:
            raise ValueError("会話が空です")

        total_chars = sum(len(m.content) for m in messages)
        chunks: list[Chunk] = []

        # 現在のチャンク用メッセージとバイト数
        current_messages: list = []
        current_chars = 0
        chunk_start_index = 0  # オーバーラップ開始位置

        for i, message in enumerate(messages):
            msg_chars = len(message.content)

            # 単一メッセージが chunk_size を超える場合
            if msg_chars >= self.chunk_size and not current_messages:
                logger.warning(
                    f"単一メッセージが chunk_size ({self.chunk_size}) を超過: "
                    f"{msg_chars} chars"
                )
                # 単独チャンクとして処理
                chunks.append(Chunk(
                    index=len(chunks),
                    messages=[message],
                    char_count=msg_chars,
                    has_overlap=len(chunks) > 0,
                    overlap_count=0,
                ))
                chunk_start_index = i + 1
                continue

            # チャンク境界を超える場合
            if current_chars + msg_chars > self.chunk_size and current_messages:
                # 現在のチャンクを確定
                overlap_count = 0
                if len(chunks) > 0:
                    # 前チャンクの末尾からのオーバーラップ数
                    overlap_count = min(
                        self.overlap_messages,
                        len(current_messages),
                    )

                chunks.append(Chunk(
                    index=len(chunks),
                    messages=list(current_messages),
                    char_count=current_chars,
                    has_overlap=len(chunks) > 0,
                    overlap_count=overlap_count,
                ))

                # 次チャンク用にオーバーラップを設定
                if self.overlap_messages > 0 and len(current_messages) > 0:
                    overlap_msgs = current_messages[-self.overlap_messages:]
                    current_messages = list(overlap_msgs)
                    current_chars = sum(len(m.content) for m in current_messages)
                else:
                    current_messages = []
                    current_chars = 0

            # メッセージ追加
            current_messages.append(message)
            current_chars += msg_chars

        # 残りのメッセージをチャンクに
        if current_messages:
            overlap_count = 0
            if len(chunks) > 0:
                overlap_count = min(
                    self.overlap_messages,
                    len(current_messages),
                )

            chunks.append(Chunk(
                index=len(chunks),
                messages=list(current_messages),
                char_count=current_chars,
                has_overlap=len(chunks) > 0,
                overlap_count=overlap_count,
            ))

        return ChunkedConversation(
            original=conversation,
            chunks=chunks,
            total_chars=total_chars,
            chunk_size=self.chunk_size,
        )

    @staticmethod
    def get_chunk_filename(title: str, chunk_index: int) -> str:
        """
        チャンク用ファイル名を生成。

        Args:
            title: 元の会話タイトル
            chunk_index: チャンク番号（0-indexed）

        Returns:
            連番付きファイル名（例: "タイトル_001.md"）
        """
        # 1-indexed で表示、3桁ゼロパディング
        return f"{title}_{chunk_index + 1:03d}.md"
