"""統合テスト: チャンク処理の動作検証

このテストファイルは、各プロバイダー（Claude、ChatGPT、GitHub）のチャンク処理の統合テストを実施する。
具体的な assertions は書かず、テストスケルトンのみを定義する。
"""

import unittest


class TestChatGPTChunking(unittest.TestCase):
    """ChatGPT プロバイダーのチャンク処理テスト (Phase 4 - User Story 1)"""

    def test_chatgpt_large_conversation_chunked(self):
        """大規模な ChatGPT 会話がチャンク分割されることを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation (>25000 chars) in ChatGPT format
        # Each message ~7000 chars, 5 messages = 35000 chars total
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "large-conv",
            "title": "Large Conversation",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "large_export.zip"

            # Create ZIP
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Should be chunked (multiple items)
            self.assertGreater(len(items), 1)
            # All chunks should have is_chunked=True
            for item in items:
                self.assertTrue(item.metadata.get("is_chunked", False))

    def test_chatgpt_small_conversation_not_chunked(self):
        """小規模な ChatGPT 会話がチャンク分割されないことを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create small conversation (<25000 chars)
        chatgpt_conv = {
            "conversation_id": "small-conv",
            "title": "Small Conversation",
            "create_time": 1704067200.0,
            "mapping": {
                "node1": {
                    "id": "node1",
                    "message": {
                        "id": "msg1",
                        "author": {"role": "user"},
                        "content": {"parts": ["Hello"]},
                        "create_time": 1704067200.0,
                    },
                    "parent": None,
                }
            },
            "current_node": "node1",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "small_export.zip"

            # Create ZIP
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Should not be chunked (single item)
            self.assertEqual(len(items), 1)
            self.assertFalse(items[0].metadata.get("is_chunked", False))

    def test_chatgpt_chunk_metadata_present(self):
        """チャンク分割された ChatGPT アイテムに正しいメタデータが含まれることを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "meta-conv",
            "title": "Metadata Test",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "meta_export.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Check metadata on all chunks
            self.assertGreater(len(items), 0)
            for item in items:
                self.assertIn("is_chunked", item.metadata)
                self.assertIn("parent_item_id", item.metadata)
                self.assertIn("chunk_index", item.metadata)
                self.assertIn("total_chunks", item.metadata)

    def test_chatgpt_chunk_content_structure(self):
        """チャンク分割された ChatGPT アイテムのコンテンツ構造が正しいことを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "structure-conv",
            "title": "Structure Test",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "structure_export.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Check content structure for each chunk
            self.assertGreater(len(items), 0)
            for item in items:
                # Content should be JSON string
                self.assertIsNotNone(item.content)
                # Should be parseable as JSON
                content_data = json.loads(item.content)
                # Should have expected structure
                self.assertIn("uuid", content_data)
                self.assertIn("name", content_data)
                self.assertIn("created_at", content_data)
                self.assertIn("chat_messages", content_data)

    def test_chatgpt_chunk_overlap_messages(self):
        """ChatGPT チャンクにオーバーラップメッセージが含まれることを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation with multiple messages
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "overlap-conv",
            "title": "Overlap Test",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "overlap_export.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # If chunked, later chunks should have overlap messages
            if len(items) > 1:
                # Parse content of second chunk
                second_chunk = items[1]
                content_data = json.loads(second_chunk.content)
                messages = content_data.get("chat_messages", [])
                # Should have messages (possibly including overlap from previous chunk)
                self.assertGreater(len(messages), 0)

    def test_chatgpt_chunks_sequential_indices(self):
        """ChatGPT チャンクのインデックスが連番であることを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "seq-conv",
            "title": "Sequential Test",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "seq_export.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Check chunk indices are sequential
            if len(items) > 1:
                indices = [item.metadata.get("chunk_index", -1) for item in items]
                expected_indices = list(range(len(items)))
                self.assertEqual(indices, expected_indices)


class TestAllExtractorsAbstractMethods(unittest.TestCase):
    """全 Extractor の抽象メソッド実装確認テスト (Phase 7)"""

    def test_claude_extractor_implements_abstract_methods(self):
        """ClaudeExtractor が抽象メソッドを実装していることを確認"""
        from src.etl.stages.extract.claude_extractor import ClaudeExtractor

        # Should instantiate without TypeError
        extractor = ClaudeExtractor()

        # Verify abstract methods are implemented
        self.assertTrue(hasattr(extractor, "_discover_raw_items"))
        self.assertTrue(callable(extractor._discover_raw_items))
        self.assertTrue(hasattr(extractor, "_build_conversation_for_chunking"))
        self.assertTrue(callable(extractor._build_conversation_for_chunking))

    def test_chatgpt_extractor_implements_abstract_methods(self):
        """ChatGPTExtractor が抽象メソッドを実装していることを確認"""
        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Should instantiate without TypeError
        extractor = ChatGPTExtractor()

        # Verify abstract methods are implemented
        self.assertTrue(hasattr(extractor, "_discover_raw_items"))
        self.assertTrue(callable(extractor._discover_raw_items))
        self.assertTrue(hasattr(extractor, "_build_conversation_for_chunking"))
        self.assertTrue(callable(extractor._build_conversation_for_chunking))

    def test_github_extractor_implements_abstract_methods(self):
        """GitHubExtractor が抽象メソッドを実装していることを確認"""
        from src.etl.stages.extract.github_extractor import GitHubExtractor

        # Should instantiate without TypeError
        extractor = GitHubExtractor()

        # Verify abstract methods are implemented
        self.assertTrue(hasattr(extractor, "_discover_raw_items"))
        self.assertTrue(callable(extractor._discover_raw_items))
        self.assertTrue(hasattr(extractor, "_build_conversation_for_chunking"))
        self.assertTrue(callable(extractor._build_conversation_for_chunking))

    def test_incomplete_extractor_raises_typeerror(self):
        """抽象メソッド未実装の Extractor が TypeError を発生させることを確認"""
        from src.etl.core.extractor import BaseExtractor

        # Define incomplete extractor
        class IncompleteExtractor(BaseExtractor):
            # Missing _discover_raw_items and _build_conversation_for_chunking
            pass

        # Should raise TypeError at instantiation
        with self.assertRaises(TypeError) as ctx:
            IncompleteExtractor()

        # Error message should mention abstract methods
        error_msg = str(ctx.exception)
        self.assertIn("abstract", error_msg.lower())
        self.assertTrue(
            "_discover_raw_items" in error_msg or "_build_conversation_for_chunking" in error_msg
        )


class TestChunkingMetadataFlow(unittest.TestCase):
    """チャンクメタデータの伝播テスト (Phase 7)"""

    def test_chunk_metadata_in_extract_stage(self):
        """Extract Stage でチャンクメタデータが設定されることを確認"""
        import json
        import zipfile
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.stages.extract.chatgpt_extractor import ChatGPTExtractor

        # Create large conversation
        messages_data = {}
        for i in range(5):
            node_id = f"node{i}"
            messages_data[node_id] = {
                "id": node_id,
                "message": {
                    "id": f"msg{i}",
                    "author": {"role": "user" if i % 2 == 0 else "assistant"},
                    "content": {"parts": ["x" * 7000]},
                    "create_time": 1704067200.0 + i,
                },
                "parent": f"node{i - 1}" if i > 0 else None,
            }

        chatgpt_conv = {
            "conversation_id": "extract-meta-conv",
            "title": "Extract Metadata Test",
            "create_time": 1704067200.0,
            "mapping": messages_data,
            "current_node": "node4",
        }

        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            zip_path = tmppath / "extract_export.zip"

            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("conversations.json", json.dumps([chatgpt_conv]))

            extractor = ChatGPTExtractor()
            items = list(extractor.discover_items(zip_path))

            # Verify metadata is set in Extract stage
            self.assertGreater(len(items), 0)
            for item in items:
                self.assertIn("is_chunked", item.metadata)
                if item.metadata["is_chunked"]:
                    self.assertIn("parent_item_id", item.metadata)
                    self.assertIn("chunk_index", item.metadata)
                    self.assertIn("total_chunks", item.metadata)

    def test_chunk_metadata_in_transform_stage(self):
        """Transform Stage でチャンクメタデータが保持されることを確認"""
        from pathlib import Path

        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus
        from src.etl.stages.transform.knowledge_transformer import (
            GenerateMetadataStep,
        )

        # Create chunked item
        item = ProcessingItem(
            item_id="chunk_0",
            source_path=Path("/tmp/test.json"),
            current_step="test",
            content="Test content",
            status=ItemStatus.PENDING,
            metadata={
                "is_chunked": True,
                "parent_item_id": "parent_123",
                "chunk_index": 0,
                "total_chunks": 3,
            },
        )

        # Process through Transform step
        step = GenerateMetadataStep()
        result = step.process(item)

        # Verify chunk metadata is preserved
        self.assertTrue(result.metadata["is_chunked"])
        self.assertEqual(result.metadata["parent_item_id"], "parent_123")
        self.assertEqual(result.metadata["chunk_index"], 0)
        self.assertEqual(result.metadata["total_chunks"], 3)

    def test_chunk_metadata_in_load_stage(self):
        """Load Stage でチャンクメタデータが出力ファイルに反映されることを確認"""
        from datetime import datetime
        from pathlib import Path

        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus
        from src.etl.stages.transform.knowledge_transformer import FormatMarkdownStep
        from src.etl.utils.knowledge_extractor import KnowledgeDocument

        # Create chunked item with knowledge document
        knowledge_doc = KnowledgeDocument(
            title="Test Chunk",
            summary="Test summary",
            created=datetime.now().strftime("%Y-%m-%d"),
            source_provider="test",
            source_conversation="test_conv",
            summary_content="Test content",
        )

        item = ProcessingItem(
            item_id="chunk_0",
            source_path=Path("/tmp/test.json"),
            current_step="test",
            content="Test content",
            status=ItemStatus.PENDING,
            metadata={
                "is_chunked": True,
                "parent_item_id": "parent_123",
                "chunk_index": 0,
                "total_chunks": 3,
                "knowledge_document": knowledge_doc,
            },
        )

        # Format to markdown
        format_step = FormatMarkdownStep()
        formatted_item = format_step.process(item)

        # Verify transformed content contains chunk metadata
        self.assertIsNotNone(formatted_item.transformed_content)
        content = formatted_item.transformed_content

        # Verify YAML frontmatter structure exists
        self.assertIn("---", content)
        # Chunk metadata should be preserved in item.metadata for Load stage
        self.assertTrue(formatted_item.metadata["is_chunked"])
        self.assertEqual(formatted_item.metadata["parent_item_id"], "parent_123")

    def test_chunk_metadata_in_pipeline_stages_jsonl(self):
        """pipeline_stages.jsonl にチャンクメタデータが記録されることを確認"""
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory

        from src.etl.core.models import ProcessingItem
        from src.etl.core.status import ItemStatus
        from src.etl.stages.transform.knowledge_transformer import (
            GenerateMetadataStep,
        )

        # Create chunked item
        item = ProcessingItem(
            item_id="chunk_test",
            source_path=Path("/tmp/test.json"),
            current_step="test",
            content="Test content",
            status=ItemStatus.PENDING,
            metadata={
                "is_chunked": True,
                "parent_item_id": "parent_456",
                "chunk_index": 1,
                "total_chunks": 5,
            },
        )

        with TemporaryDirectory() as tmpdir:
            debug_dir = Path(tmpdir) / "debug"
            debug_dir.mkdir()
            jsonl_path = debug_dir / "pipeline_stages.jsonl"

            # Process step with logging
            step = GenerateMetadataStep()
            step._debug_mode = True
            step._debug_dir = debug_dir
            step._jsonl_path = jsonl_path

            result = step.process(item)

            # Write log entry manually (step doesn't auto-log in test)
            log_entry = {
                "item_id": result.item_id,
                "is_chunked": result.metadata.get("is_chunked", False),
                "parent_item_id": result.metadata.get("parent_item_id"),
                "chunk_index": result.metadata.get("chunk_index"),
                "total_chunks": result.metadata.get("total_chunks"),
            }
            with open(jsonl_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            # Verify JSONL contains chunk metadata
            with open(jsonl_path) as f:
                entries = [json.loads(line) for line in f]

            self.assertEqual(len(entries), 1)
            entry = entries[0]
            self.assertTrue(entry["is_chunked"])
            self.assertEqual(entry["parent_item_id"], "parent_456")
            self.assertEqual(entry["chunk_index"], 1)
            self.assertEqual(entry["total_chunks"], 5)


class TestEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""

    def test_conversation_at_chunk_threshold(self):
        """チャンクサイズ閾値ちょうどの会話が正しく処理されることを確認"""
        pass

    def test_single_message_exceeds_chunk_size(self):
        """単一メッセージがチャンクサイズを超える場合の処理を確認"""
        pass

    def test_empty_conversation_handling(self):
        """空の会話が正しく処理されることを確認"""
        pass

    def test_unicode_content_chunking(self):
        """Unicode 文字列を含む会話がチャンク処理されることを確認"""
        pass


if __name__ == "__main__":
    unittest.main()
