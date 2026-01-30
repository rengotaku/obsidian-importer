"""
llm_import.tests.test_chunker - チャンク分割モジュールのテスト
"""
from __future__ import annotations

import unittest
from dataclasses import dataclass

from scripts.llm_import.base import BaseMessage, BaseConversation
from scripts.llm_import.common.chunker import (
    Chunk,
    ChunkedConversation,
    ChunkResult,
    Chunker,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class TestMessage(BaseMessage):
    """テスト用メッセージ実装"""
    sender: str

    @property
    def role(self) -> str:
        return self.sender


@dataclass
class TestConversation(BaseConversation):
    """テスト用会話実装"""
    uuid: str
    _messages: list = None

    def __post_init__(self):
        if self._messages is None:
            self._messages = []

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def id(self) -> str:
        return self.uuid

    @property
    def provider(self) -> str:
        return "test"


def create_message(content: str, sender: str = "user") -> TestMessage:
    """テスト用メッセージ作成ヘルパー"""
    return TestMessage(
        content=content,
        timestamp="2026-01-17T10:00:00",
        sender=sender,
    )


def create_conversation(
    messages: list[TestMessage],
    title: str = "Test Conversation",
    uuid: str = "test-uuid",
) -> TestConversation:
    """テスト用会話作成ヘルパー"""
    return TestConversation(
        title=title,
        created_at="2026-01-17T10:00:00",
        uuid=uuid,
        _messages=messages,
    )


# =============================================================================
# Test Cases: Chunker Core
# =============================================================================


class TestChunkerShouldChunk(unittest.TestCase):
    """T007: should_chunk() のテスト"""

    def test_should_chunk_large_conversation(self):
        """大きい会話（>= chunk_size）はチャンク対象"""
        # 30,000文字のメッセージを作成
        large_content = "x" * 30000
        messages = [create_message(large_content)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=25000)
        self.assertTrue(chunker.should_chunk(conversation))

    def test_should_not_chunk_small_conversation(self):
        """T011: 小さい会話（< chunk_size）はチャンク不要"""
        small_content = "x" * 1000
        messages = [create_message(small_content)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=25000)
        self.assertFalse(chunker.should_chunk(conversation))

    def test_should_chunk_exactly_at_threshold(self):
        """閾値ちょうど（== chunk_size）もチャンク対象"""
        exact_content = "x" * 25000
        messages = [create_message(exact_content)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=25000)
        self.assertTrue(chunker.should_chunk(conversation))


class TestChunkerSplit(unittest.TestCase):
    """T008-T009: split() のテスト"""

    def test_split_creates_chunks_at_message_boundary(self):
        """T008: メッセージ境界で分割される"""
        # 各10,000文字のメッセージ4つ（計40,000文字）
        messages = [create_message("x" * 10000) for _ in range(4)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=25000, overlap_messages=0)
        result = chunker.split(conversation)

        # 2チャンク（20000 + 20000）に分割されるはず
        self.assertEqual(len(result.chunks), 2)
        self.assertEqual(len(result.chunks[0].messages), 2)
        self.assertEqual(len(result.chunks[1].messages), 2)

    def test_split_includes_overlap(self):
        """T009: オーバーラップが含まれる"""
        # 各8,000文字のメッセージ5つ（計40,000文字）
        messages = [create_message("x" * 8000) for _ in range(5)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=20000, overlap_messages=2)
        result = chunker.split(conversation)

        # チャンク数を確認
        self.assertGreater(len(result.chunks), 1)

        # 2つ目以降のチャンクにはオーバーラップがある
        for i in range(1, len(result.chunks)):
            chunk = result.chunks[i]
            self.assertTrue(chunk.has_overlap)
            self.assertGreater(chunk.overlap_count, 0)

    def test_split_first_chunk_no_overlap(self):
        """最初のチャンクはオーバーラップなし"""
        messages = [create_message("x" * 8000) for _ in range(5)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=20000, overlap_messages=2)
        result = chunker.split(conversation)

        first_chunk = result.chunks[0]
        self.assertFalse(first_chunk.has_overlap)
        self.assertEqual(first_chunk.overlap_count, 0)

    def test_split_empty_conversation_raises_error(self):
        """T020: 空の会話は ValueError"""
        conversation = create_conversation([])
        chunker = Chunker()

        with self.assertRaises(ValueError) as ctx:
            chunker.split(conversation)
        self.assertIn("空", str(ctx.exception))

    def test_split_single_message_exceeds_chunk_size(self):
        """T015: 単一メッセージが chunk_size を超える場合"""
        # 1つの超大きいメッセージ
        huge_content = "x" * 50000
        messages = [create_message(huge_content)]
        conversation = create_conversation(messages)

        chunker = Chunker(chunk_size=25000)
        result = chunker.split(conversation)

        # 1チャンクとして処理される
        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(result.chunks[0].char_count, 50000)

    def test_split_preserves_original_conversation(self):
        """元の会話データが保持される"""
        messages = [create_message("x" * 15000) for _ in range(3)]
        conversation = create_conversation(messages, title="Original Title")

        chunker = Chunker(chunk_size=25000)
        result = chunker.split(conversation)

        self.assertEqual(result.original.title, "Original Title")
        self.assertEqual(result.total_chars, 45000)
        self.assertEqual(result.chunk_size, 25000)


class TestChunkerGetChunkFilename(unittest.TestCase):
    """T010: get_chunk_filename() のテスト"""

    def test_get_chunk_filename_format(self):
        """ファイル名フォーマットが正しい"""
        self.assertEqual(
            Chunker.get_chunk_filename("長い会話", 0),
            "長い会話_001.md",
        )
        self.assertEqual(
            Chunker.get_chunk_filename("長い会話", 1),
            "長い会話_002.md",
        )
        self.assertEqual(
            Chunker.get_chunk_filename("長い会話", 9),
            "長い会話_010.md",
        )

    def test_get_chunk_filename_three_digit_padding(self):
        """3桁ゼロパディング"""
        self.assertEqual(
            Chunker.get_chunk_filename("Title", 99),
            "Title_100.md",
        )


# =============================================================================
# Test Cases: Data Classes
# =============================================================================


class TestChunkDataClass(unittest.TestCase):
    """Chunk データクラスのテスト"""

    def test_chunk_creation(self):
        """Chunk が正しく作成される"""
        messages = [create_message("Hello")]
        chunk = Chunk(
            index=0,
            messages=messages,
            char_count=5,
            has_overlap=False,
            overlap_count=0,
        )
        self.assertEqual(chunk.index, 0)
        self.assertEqual(len(chunk.messages), 1)
        self.assertEqual(chunk.char_count, 5)


class TestChunkResultDataClass(unittest.TestCase):
    """ChunkResult データクラスのテスト"""

    def test_chunk_result_success(self):
        """成功時の ChunkResult"""
        result = ChunkResult(
            chunk_index=0,
            success=True,
            summary="サマリー",
            learnings=["学び1", "学び2"],
        )
        self.assertTrue(result.success)
        self.assertEqual(result.summary, "サマリー")
        self.assertIsNone(result.error)

    def test_chunk_result_failure(self):
        """失敗時の ChunkResult"""
        result = ChunkResult(
            chunk_index=0,
            success=False,
            error="処理失敗",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "処理失敗")


class TestChunkedConversationDataClass(unittest.TestCase):
    """ChunkedConversation データクラスのテスト"""

    def test_chunked_conversation_creation(self):
        """ChunkedConversation が正しく作成される"""
        messages = [create_message("x" * 15000) for _ in range(3)]
        conversation = create_conversation(messages)

        chunks = [
            Chunk(index=0, messages=messages[:2], char_count=30000, has_overlap=False, overlap_count=0),
            Chunk(index=1, messages=messages[1:], char_count=30000, has_overlap=True, overlap_count=1),
        ]

        chunked = ChunkedConversation(
            original=conversation,
            chunks=chunks,
            total_chars=45000,
            chunk_size=25000,
        )

        self.assertEqual(len(chunked.chunks), 2)
        self.assertEqual(chunked.total_chars, 45000)


if __name__ == "__main__":
    unittest.main()
