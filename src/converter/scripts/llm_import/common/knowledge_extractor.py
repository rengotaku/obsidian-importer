"""
llm_import.common.knowledge_extractor - 知識抽出ロジック

会話データから知識を抽出し、構造化された KnowledgeDocument を生成する。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from scripts.llm_import.base import BaseConversation
from scripts.llm_import.common.ollama import call_ollama, parse_json_response
from scripts.llm_import.common.chunker import Chunker, Chunk, ChunkedConversation

import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Frontmatter Helpers
# =============================================================================


def extract_file_id_from_frontmatter(content: str) -> str | None:
    """
    Markdown ファイルの frontmatter から file_id を抽出する (T021)

    Args:
        content: Markdown ファイルの内容

    Returns:
        file_id (12文字の16進数) または None

    Example:
        >>> content = "---\\ntitle: Test\\nfile_id: a1b2c3d4e5f6\\n---\\n# Content"
        >>> extract_file_id_from_frontmatter(content)
        'a1b2c3d4e5f6'
    """
    # frontmatter を抽出 (--- で囲まれた部分)
    frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # file_id を抽出
    file_id_match = re.search(r"^file_id:\s*([a-f0-9]{12})\s*$", frontmatter, re.MULTILINE)
    if file_id_match:
        return file_id_match.group(1)

    return None

# =============================================================================
# Configuration
# =============================================================================

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
KNOWLEDGE_PROMPT_PATH = PROMPTS_DIR / "knowledge_extraction.txt"
SUMMARY_PROMPT_PATH = PROMPTS_DIR / "summary_translation.txt"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class CodeSnippet:
    """
    抽出されたコードスニペット

    Attributes:
        language: プログラミング言語
        code: コード本文
        description: コードの説明
    """
    language: str
    code: str
    description: str = ""


@dataclass
class KnowledgeDocument:
    """
    抽出されたナレッジドキュメント

    Attributes:
        title: タイトル
        summary: 1行の要約（frontmatter 用）
        created: 作成日（YYYY-MM-DD）
        source_provider: プロバイダー名
        source_conversation: 元の会話ID
        summary_content: 構造化されたまとめ
        key_learnings: 主要な学び
        code_snippets: コードスニペット
        file_id: ファイル追跡用ハッシュID（12文字16進数）
        normalized: 正規化フラグ
    """
    title: str
    summary: str
    created: str
    source_provider: str
    source_conversation: str
    summary_content: str
    key_learnings: list[str]
    code_snippets: list[CodeSnippet] = field(default_factory=list)
    file_id: str = ""
    normalized: bool = False

    def to_markdown(self) -> str:
        """
        Markdown 形式に変換

        Returns:
            Markdown 形式の文字列
        """
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append(f"title: {self.title}")
        lines.append(f"summary: {self.summary}")
        lines.append(f"created: {self.created}")
        lines.append(f"source_provider: {self.source_provider}")
        lines.append(f"source_conversation: {self.source_conversation}")
        if self.file_id:
            lines.append(f"file_id: {self.file_id}")
        lines.append(f"normalized: {str(self.normalized).lower()}")
        lines.append("---")
        lines.append("")

        # まとめ
        lines.append("# まとめ")
        lines.append("")
        # summary_content 内の見出しを ## 以下に正規化
        normalized_content = self._normalize_summary_headings(self.summary_content)
        lines.append(normalized_content)
        lines.append("")

        # 主要な学び
        lines.append("# 主要な学び")
        lines.append("")
        for learning in self.key_learnings:
            lines.append(f"- {learning}")
        lines.append("")

        # コードスニペット
        if self.code_snippets:
            lines.append("# コードスニペット")
            lines.append("")
            for snippet in self.code_snippets:
                if snippet.description:
                    lines.append(f"## {snippet.description}")
                    lines.append("")
                lines.append(f"```{snippet.language}")
                lines.append(snippet.code)
                lines.append("```")
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _normalize_summary_headings(content: str) -> str:
        """
        summary_content 内の見出しを ## 以下に正規化

        - # → ##
        - ## → ###
        - など（相対的な階層を維持）
        """
        import re

        lines = content.split("\n")
        result_lines = []

        for line in lines:
            match = re.match(r"^(#{1,6})(\s+.*)$", line)
            if match:
                hashes = match.group(1)
                rest = match.group(2)
                # 見出しレベルを1つ下げる（最大6）
                new_level = min(len(hashes) + 1, 6)
                result_lines.append("#" * new_level + rest)
            else:
                result_lines.append(line)

        return "\n".join(result_lines)


@dataclass
class ExtractionResult:
    """
    抽出結果

    Attributes:
        success: 成功フラグ
        document: 抽出されたドキュメント（成功時）
        error: エラーメッセージ（失敗時）
        raw_response: 生のLLMレスポンス
        user_prompt: LLMに送信したプロンプト（エラーデバッグ用）
    """
    success: bool
    document: KnowledgeDocument | None = None
    error: str | None = None
    raw_response: str | None = None
    user_prompt: str | None = None


# =============================================================================
# Knowledge Extractor
# =============================================================================


class KnowledgeExtractor:
    """
    会話から知識を抽出

    Ollama API を使用して会話データを分析し、
    構造化された KnowledgeDocument を生成する。

    2段階 LLM 処理:
    - Summary あり: Step 1 (翻訳) + Step 2 (まとめ生成)
    - Summary なし: Step 1 のみ (まとめ生成 + summary)
    """

    # 英語サマリー検出パターン
    ENGLISH_SUMMARY_PATTERNS = [
        r"^\*\*Conversation Overview\*\*",  # Claude summary format
        r"^Conversation Overview",
        r"^Summary:",
        r"^Overview:",
        r"^The user (asked|requested|wanted|discussed)",
    ]

    def __init__(
        self,
        prompt_path: Path | None = None,
        summary_prompt_path: Path | None = None,
        chunk_size: int = 25000,
        overlap_messages: int = 2,
    ):
        """
        Args:
            prompt_path: 知識抽出プロンプトファイルのパス（省略時はデフォルト）
            summary_prompt_path: 翻訳プロンプトファイルのパス（省略時はデフォルト）
            chunk_size: チャンクサイズ閾値（文字数、デフォルト: 25000）
            overlap_messages: オーバーラップするメッセージ数（デフォルト: 2）
        """
        self.prompt_path = prompt_path or KNOWLEDGE_PROMPT_PATH
        self.summary_prompt_path = summary_prompt_path or SUMMARY_PROMPT_PATH
        self._system_prompt: str | None = None
        self._summary_prompt: str | None = None
        self.chunker = Chunker(chunk_size=chunk_size, overlap_messages=overlap_messages)

    @property
    def system_prompt(self) -> str:
        """システムプロンプトを取得（遅延ロード）"""
        if self._system_prompt is None:
            with open(self.prompt_path, encoding="utf-8") as f:
                self._system_prompt = f.read()
        return self._system_prompt

    @property
    def summary_system_prompt(self) -> str:
        """翻訳用システムプロンプトを取得（遅延ロード）"""
        if self._summary_prompt is None:
            with open(self.summary_prompt_path, encoding="utf-8") as f:
                self._summary_prompt = f.read()
        return self._summary_prompt

    def is_english_summary(self, text: str | None) -> bool:
        """
        サマリーが英語かどうかを判定

        Args:
            text: サマリーテキスト

        Returns:
            英語サマリーの場合 True
        """
        if not text:
            return False

        # パターンマッチ
        for pattern in self.ENGLISH_SUMMARY_PATTERNS:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                return True

        # ASCII 文字比率による判定（70%以上が ASCII なら英語と判定）
        ascii_chars = sum(1 for c in text if ord(c) < 128)
        total_chars = len(text)
        if total_chars > 0 and ascii_chars / total_chars > 0.7:
            return True

        return False

    def translate_summary(self, summary: str) -> tuple[str | None, str | None]:
        """
        英語サマリーを日本語に翻訳 (Step 1)

        Args:
            summary: 英語のサマリー

        Returns:
            (翻訳されたサマリー, エラーメッセージ)
        """
        response, error = call_ollama(
            self.summary_system_prompt,
            f"以下の英語サマリーを日本語に翻訳してください:\n\n{summary}"
        )

        if error:
            return None, error

        data, parse_error = parse_json_response(response)
        if parse_error:
            return None, parse_error

        return data.get("summary", ""), None

    def extract(self, conversation: BaseConversation) -> ExtractionResult:
        """
        会話から知識を抽出

        2段階フロー:
        - Summary あり: Step 1 (翻訳) → Step 2 (まとめ生成)
        - Summary なし: Step 1 のみ (まとめ生成 + summary)

        Args:
            conversation: 会話データ

        Returns:
            ExtractionResult
        """
        summary = getattr(conversation, "summary", None)
        has_english_summary = summary and self.is_english_summary(summary)

        translated_summary: str | None = None

        # Step 1: Summary がある場合は翻訳
        if has_english_summary:
            translated_summary, translate_error = self.translate_summary(summary)
            if translate_error:
                return ExtractionResult(
                    success=False,
                    error=f"Summary 翻訳エラー: {translate_error}",
                )

        # Step 2: まとめ生成（Summary を除いた会話内容で呼び出し）
        user_message = self._build_user_message(
            conversation,
            exclude_summary=has_english_summary,
        )

        response, error = call_ollama(self.system_prompt, user_message)

        if error:
            return ExtractionResult(
                success=False,
                error=error,
                raw_response=response,
                user_prompt=user_message,
            )

        # JSON をパース
        data, parse_error = parse_json_response(response)

        if parse_error:
            return ExtractionResult(
                success=False,
                error=parse_error,
                raw_response=response,
                user_prompt=user_message,
            )

        # KnowledgeDocument を構築
        try:
            document = self._build_document(
                data,
                conversation,
                translated_summary=translated_summary,
            )
            return ExtractionResult(
                success=True,
                document=document,
                raw_response=response,
                user_prompt=user_message,
            )
        except (KeyError, ValueError) as e:
            return ExtractionResult(
                success=False,
                error=f"ドキュメント構築エラー: {e}",
                raw_response=response,
                user_prompt=user_message,
            )

    def _build_user_message(
        self,
        conversation: BaseConversation,
        exclude_summary: bool = False,
    ) -> str:
        """
        ユーザーメッセージを構築

        Args:
            conversation: 会話データ
            exclude_summary: True の場合、サマリーを含めない（Step 2 用）

        Returns:
            ユーザーメッセージ
        """
        lines = []

        # メタ情報
        lines.append(f"ファイル名: {conversation.title}")
        lines.append(f"プロバイダー: {conversation.provider}")

        # サマリー（exclude_summary=True の場合は含めない）
        summary = getattr(conversation, "summary", None)
        if not exclude_summary and summary:
            lines.append(f"会話サマリー: {summary}")
        else:
            lines.append("会話サマリー: なし")

        lines.append(f"メッセージ数: {len(conversation.messages)}")
        lines.append(f"会話作成日: {conversation.created_at}")
        lines.append("")
        lines.append("--- 会話内容 ---")
        lines.append("")

        # 会話内容
        for msg in conversation.messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            lines.append(f"[{role_label}]")
            lines.append(msg.content.strip())
            lines.append("")

        return "\n".join(lines)

    def _build_document(
        self,
        data: dict,
        conversation: BaseConversation,
        translated_summary: str | None = None,
    ) -> KnowledgeDocument:
        """
        LLM出力から KnowledgeDocument を構築

        Args:
            data: パース済みの LLM 出力
            conversation: 元の会話データ
            translated_summary: 翻訳済みサマリー（Step 1 の結果）

        Returns:
            KnowledgeDocument
        """
        # コードスニペットを変換
        code_snippets = []
        for snippet_data in data.get("code_snippets", []):
            if isinstance(snippet_data, dict):
                code_snippets.append(CodeSnippet(
                    language=snippet_data.get("language", ""),
                    code=snippet_data.get("code", ""),
                    description=snippet_data.get("description", ""),
                ))

        # 作成日を抽出（ISO形式から YYYY-MM-DD）
        created = conversation.created_at[:10] if conversation.created_at else ""

        # タイトル: 会話タイトルから日付プレフィックスを除去
        title = self._clean_title(conversation.title)

        # summary: 翻訳済みサマリーがあればそれを使用、なければ LLM 出力を使用
        summary = translated_summary or data.get("summary", "")

        return KnowledgeDocument(
            title=title,
            summary=summary,
            created=created,
            source_provider=conversation.provider,
            source_conversation=conversation.id,
            summary_content=data.get("summary_content", ""),
            key_learnings=data.get("key_learnings", []),
            code_snippets=code_snippets,
            normalized=False,
        )

    def _clean_title(self, title: str) -> str:
        """
        タイトルから日付プレフィックスを除去

        Args:
            title: 元のタイトル

        Returns:
            クリーンなタイトル
        """
        # YYYY-MM-DD_ または YYYY-MM-DD プレフィックスを除去
        cleaned = re.sub(r"^\d{4}-\d{2}-\d{2}_?", "", title)
        return cleaned.strip() or title

    def should_chunk(self, conversation: BaseConversation) -> bool:
        """
        会話がチャンク分割対象か判定

        Args:
            conversation: 会話データ

        Returns:
            True: チャンク分割が必要
            False: 通常処理で可能
        """
        return self.chunker.should_chunk(conversation)

    def extract_chunked(
        self,
        conversation: BaseConversation,
    ) -> list[tuple[str, ExtractionResult]]:
        """
        大規模会話をチャンク分割して抽出

        Args:
            conversation: 会話データ（チャンク分割対象）

        Returns:
            list[tuple[str, ExtractionResult]]: (ファイル名, 抽出結果) のリスト
        """
        chunked = self.chunker.split(conversation)
        total_chunks = len(chunked.chunks)

        logger.info(
            f"チャンク分割: {total_chunks} チャンク（総文字数: {chunked.total_chars:,}）"
        )

        results: list[tuple[str, ExtractionResult]] = []

        for chunk in chunked.chunks:
            chunk_num = chunk.index + 1
            logger.info(f"チャンク {chunk_num}/{total_chunks} 処理中...")

            # チャンク用の一時的な会話オブジェクトを作成
            result = self._extract_chunk(chunk, conversation)

            # ファイル名を生成
            base_title = self._clean_title(conversation.title)
            filename = Chunker.get_chunk_filename(base_title, chunk.index)

            if result.success:
                logger.info(f"チャンク {chunk_num}/{total_chunks} 完了 → {filename}")
            else:
                logger.error(
                    f"チャンク {chunk_num}/{total_chunks} 失敗: {result.error}"
                )

            results.append((filename, result))

        return results

    def _extract_chunk(
        self,
        chunk: Chunk,
        original_conversation: BaseConversation,
    ) -> ExtractionResult:
        """
        単一チャンクを抽出処理

        Args:
            chunk: 処理対象のチャンク
            original_conversation: 元の会話（メタデータ用）

        Returns:
            ExtractionResult
        """
        # チャンク用のユーザーメッセージを構築
        user_message = self._build_chunk_user_message(
            chunk,
            original_conversation,
        )

        response, error = call_ollama(self.system_prompt, user_message)

        if error:
            return ExtractionResult(
                success=False,
                error=error,
                raw_response=response,
            )

        # JSON をパース
        data, parse_error = parse_json_response(response)

        if parse_error:
            return ExtractionResult(
                success=False,
                error=parse_error,
                raw_response=response,
            )

        # KnowledgeDocument を構築
        try:
            document = self._build_chunk_document(
                data,
                chunk,
                original_conversation,
            )
            return ExtractionResult(
                success=True,
                document=document,
                raw_response=response,
            )
        except (KeyError, ValueError) as e:
            return ExtractionResult(
                success=False,
                error=f"ドキュメント構築エラー: {e}",
                raw_response=response,
            )

    def _build_chunk_user_message(
        self,
        chunk: Chunk,
        original_conversation: BaseConversation,
    ) -> str:
        """
        チャンク用のユーザーメッセージを構築

        Args:
            chunk: 処理対象のチャンク
            original_conversation: 元の会話（メタデータ用）

        Returns:
            ユーザーメッセージ
        """
        lines = []

        # メタ情報
        chunk_num = chunk.index + 1
        lines.append(f"ファイル名: {original_conversation.title} (チャンク {chunk_num})")
        lines.append(f"プロバイダー: {original_conversation.provider}")
        lines.append("会話サマリー: なし")
        lines.append(f"メッセージ数: {len(chunk.messages)}")
        lines.append(f"会話作成日: {original_conversation.created_at}")

        if chunk.has_overlap:
            lines.append(f"※ 前チャンクからのオーバーラップ: {chunk.overlap_count} メッセージ")

        lines.append("")
        lines.append("--- 会話内容 ---")
        lines.append("")

        # 会話内容
        for msg in chunk.messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            lines.append(f"[{role_label}]")
            lines.append(msg.content.strip())
            lines.append("")

        return "\n".join(lines)

    def _build_chunk_document(
        self,
        data: dict,
        chunk: Chunk,
        original_conversation: BaseConversation,
    ) -> KnowledgeDocument:
        """
        チャンク用の KnowledgeDocument を構築

        Args:
            data: パース済みの LLM 出力
            chunk: 処理対象のチャンク
            original_conversation: 元の会話データ

        Returns:
            KnowledgeDocument
        """
        # コードスニペットを変換
        code_snippets = []
        for snippet_data in data.get("code_snippets", []):
            if isinstance(snippet_data, dict):
                code_snippets.append(CodeSnippet(
                    language=snippet_data.get("language", ""),
                    code=snippet_data.get("code", ""),
                    description=snippet_data.get("description", ""),
                ))

        # 作成日を抽出（ISO形式から YYYY-MM-DD）
        created = original_conversation.created_at[:10] if original_conversation.created_at else ""

        # タイトル: 会話タイトルから日付プレフィックスを除去 + チャンク番号
        base_title = self._clean_title(original_conversation.title)
        chunk_num = chunk.index + 1
        title = f"{base_title} (Part {chunk_num})"

        # summary: LLM 出力を使用
        summary = data.get("summary", "")

        return KnowledgeDocument(
            title=title,
            summary=summary,
            created=created,
            source_provider=original_conversation.provider,
            source_conversation=f"{original_conversation.id}#chunk{chunk.index}",
            summary_content=data.get("summary_content", ""),
            key_learnings=data.get("key_learnings", []),
            code_snippets=code_snippets,
            normalized=False,
        )
