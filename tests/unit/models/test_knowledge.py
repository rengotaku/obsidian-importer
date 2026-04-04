"""Tests for LLMKnowledge dataclass validation.

Issue #98: LLM が必須フィールドを返さなかった場合の検証
"""

import unittest

from obsidian_etl.models.knowledge import LLMFieldValidationError, LLMKnowledge


class TestLLMKnowledge(unittest.TestCase):
    """LLMKnowledge: バリデーション付き構造体。"""

    def test_valid_knowledge(self):
        """全フィールドが有効な場合、正常に構築されること。"""
        k = LLMKnowledge(
            title="タイトル",
            summary="要約。",
            summary_content="内容。",
            tags=["タグ1"],
        )
        self.assertEqual(k.title, "タイトル")
        self.assertEqual(k.summary, "要約。")
        self.assertEqual(k.summary_content, "内容。")
        self.assertEqual(k.tags, ["タグ1"])

    def test_empty_title_raises(self):
        """title が空の場合、LLMFieldValidationError が発生すること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="", summary="要約。", summary_content="内容。", tags=["タグ"])
        self.assertIn("title", ctx.exception.missing_fields)

    def test_whitespace_only_title_raises(self):
        """title が空白のみの場合、LLMFieldValidationError が発生すること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="   ", summary="要約。", summary_content="内容。", tags=["タグ"])
        self.assertIn("title", ctx.exception.missing_fields)

    def test_empty_summary_raises(self):
        """summary が空の場合、LLMFieldValidationError が発生すること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="タイトル", summary="", summary_content="内容。", tags=["タグ"])
        self.assertIn("summary", ctx.exception.missing_fields)

    def test_empty_summary_content_raises(self):
        """summary_content が空の場合、LLMFieldValidationError が発生すること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="タイトル", summary="要約。", summary_content="", tags=["タグ"])
        self.assertIn("summary_content", ctx.exception.missing_fields)

    def test_empty_tags_raises(self):
        """tags が空リストの場合、LLMFieldValidationError が発生すること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="タイトル", summary="要約。", summary_content="内容。", tags=[])
        self.assertIn("tags", ctx.exception.missing_fields)

    def test_multiple_empty_fields(self):
        """複数フィールドが空の場合、すべてが missing_fields に含まれること。"""
        with self.assertRaises(LLMFieldValidationError) as ctx:
            LLMKnowledge(title="", summary="", summary_content="内容。", tags=[])
        self.assertEqual(sorted(ctx.exception.missing_fields), ["summary", "tags", "title"])

    def test_frozen_immutable(self):
        """frozen=True でフィールド変更不可であること。"""
        k = LLMKnowledge(
            title="タイトル", summary="要約。", summary_content="内容。", tags=["タグ"]
        )
        with self.assertRaises(AttributeError):
            k.title = "新タイトル"  # type: ignore[misc]

    def test_to_generated_metadata(self):
        """to_generated_metadata が正しい dict を返すこと。"""
        k = LLMKnowledge(
            title="タイトル", summary="要約。", summary_content="内容。", tags=["タグ1", "タグ2"]
        )
        meta = k.to_generated_metadata()
        self.assertEqual(meta["title"], "タイトル")
        self.assertEqual(meta["summary"], "要約。")
        self.assertEqual(meta["summary_content"], "内容。")
        self.assertEqual(meta["tags"], ["タグ1", "タグ2"])

    def test_from_dict(self):
        """from_dict で dict から構築できること。"""
        data = {
            "title": "タイトル",
            "summary": "要約。",
            "summary_content": "内容。",
            "tags": ["タグ"],
        }
        k = LLMKnowledge.from_dict(data)
        self.assertEqual(k.title, "タイトル")

    def test_from_dict_missing_key_raises(self):
        """from_dict でキーが不足している場合、バリデーションエラーになること。"""
        with self.assertRaises(LLMFieldValidationError):
            LLMKnowledge.from_dict({"title": "タイトル"})

    def test_with_summary(self):
        """with_summary で summary を差し替えた新インスタンスが返ること。"""
        k = LLMKnowledge(
            title="タイトル", summary="英語要約。", summary_content="内容。", tags=["タグ"]
        )
        k2 = k.with_summary("翻訳後の要約。")
        self.assertEqual(k2.summary, "翻訳後の要約。")
        self.assertEqual(k.summary, "英語要約。")  # 元は変更なし
        self.assertEqual(k2.title, "タイトル")  # 他フィールドは維持


if __name__ == "__main__":
    unittest.main()
