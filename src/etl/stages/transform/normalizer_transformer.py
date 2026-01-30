"""NormalizerTransformer stage for ETL pipeline.

Normalizes Markdown files to Obsidian format with proper frontmatter.
"""

import json
import re
from datetime import datetime

from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.types import StageType
from src.etl.utils.ollama import call_ollama


class ClassifyGenreStep(BaseStep):
    """Classify document genre.

    Note: This is a stub implementation. Full implementation will
    use Ollama for LLM-based classification.
    """

    # Genre keywords for simple classification
    GENRE_KEYWORDS = {
        "engineer": [
            "python",
            "code",
            "programming",
            "api",
            "database",
            "function",
            "class",
            "algorithm",
            "developer",
            "software",
            "git",
            "docker",
        ],
        "business": [
            "meeting",
            "project",
            "strategy",
            "management",
            "client",
            "sales",
            "marketing",
            "budget",
            "roi",
            "kpi",
        ],
        "economy": [
            "market",
            "stock",
            "investment",
            "economic",
            "gdp",
            "inflation",
            "trade",
            "finance",
        ],
        "daily": [
            "today",
            "personal",
            "diary",
            "memo",
            "note",
            "reminder",
            "shopping",
        ],
    }

    @property
    def name(self) -> str:
        return "classify_genre"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Classify document genre based on content.

        This is a simple keyword-based classification.
        Full implementation will use Ollama.

        Args:
            item: Item with content.

        Returns:
            Item with genre classification.
        """
        content = (item.content or "").lower()

        # Count keyword matches for each genre
        scores = {}
        for genre, keywords in self.GENRE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                scores[genre] = score

        # Determine genre
        if scores:
            best_genre = max(scores, key=scores.get)
            confidence = scores[best_genre] / (sum(scores.values()) or 1)
            item.metadata["genre"] = best_genre
            item.metadata["genre_confidence"] = confidence
        else:
            item.metadata["genre"] = "other"
            item.metadata["genre_confidence"] = 0.0

        return item


class NormalizeFrontmatterStep(BaseStep):
    """Normalize YAML frontmatter."""

    @property
    def name(self) -> str:
        return "normalize_frontmatter"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Normalize frontmatter to standard format.

        Args:
            item: Item with content.

        Returns:
            Item with normalized frontmatter.
        """
        content = item.content or ""
        lines = content.split("\n")

        # Check if already has frontmatter
        has_frontmatter = lines and lines[0].strip() == "---"

        existing_frontmatter = {}
        body_start = 0

        if has_frontmatter:
            # Find end of frontmatter
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    body_start = i + 1
                    # Parse existing frontmatter (simple YAML parser)
                    current_key = None
                    for fm_line in lines[1:i]:
                        stripped = fm_line.strip()
                        if not stripped:
                            continue

                        # List item: "  - value"
                        if stripped.startswith("- "):
                            if current_key and isinstance(
                                existing_frontmatter.get(current_key), list
                            ):
                                existing_frontmatter[current_key].append(stripped[2:].strip())
                        # Key: value or Key:
                        elif ":" in fm_line:
                            key, _, value = fm_line.partition(":")
                            key = key.strip()
                            value = value.strip()
                            if value:
                                # Key: value
                                existing_frontmatter[key] = value
                            else:
                                # Key: (list follows)
                                existing_frontmatter[key] = []
                                current_key = key
                    break
            else:
                # No closing delimiter found
                body_start = 0
                has_frontmatter = False

        # Get body content
        body = "\n".join(lines[body_start:]).strip()

        # Extract title from first heading if not in frontmatter
        title = existing_frontmatter.get("title", "")
        if not title:
            # Look for first heading
            heading_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
            else:
                # Use filename as title
                title = item.source_path.stem

        # Build normalized frontmatter
        normalized = {
            "title": title,
            "created": existing_frontmatter.get("created", datetime.now().strftime("%Y-%m-%d")),
        }

        # Preserve summary (必須)
        if "summary" in existing_frontmatter:
            normalized["summary"] = existing_frontmatter["summary"]

        # Preserve or generate tags
        if "tags" in existing_frontmatter:
            normalized["tags"] = existing_frontmatter["tags"]
        else:
            # Generate tags using LLM
            generated_tags = self._generate_tags_with_llm(item)
            if generated_tags:
                normalized["tags"] = generated_tags

        # Preserve source metadata (トレーサビリティ)
        if "source_provider" in existing_frontmatter:
            normalized["source_provider"] = existing_frontmatter["source_provider"]

        if "item_id" in existing_frontmatter:
            normalized["item_id"] = existing_frontmatter["item_id"]

        # Preserve related links (関連ノート)
        if "related" in existing_frontmatter:
            normalized["related"] = existing_frontmatter["related"]

        # Build frontmatter string
        fm_lines = ["---"]
        for key, value in normalized.items():
            if key in ("tags", "related") and isinstance(value, list):
                # Format as YAML list
                fm_lines.append(f"{key}:")
                for list_item in value:
                    fm_lines.append(f"  - {list_item}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")

        item.transformed_content = "\n".join(fm_lines) + "\n\n" + body

        return item

    def _generate_tags_with_llm(self, item: ProcessingItem) -> list[str] | None:
        """Generate tags using LLM based on content.

        Args:
            item: Item with content and frontmatter.

        Returns:
            List of tags, or None if generation fails.
        """
        # Get frontmatter and body content
        content = item.content or ""
        lines = content.split("\n")

        # Parse frontmatter for title and summary
        title = ""
        summary = ""
        body_preview = ""

        has_frontmatter = lines and lines[0].strip() == "---"
        if has_frontmatter:
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    # Get body preview (first 300 chars)
                    body_start = i + 1
                    body_lines = lines[body_start:]
                    body_text = "\n".join(body_lines)
                    body_preview = body_text[:300] + "..." if len(body_text) > 300 else body_text
                    break
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("summary:"):
                    summary = line.split(":", 1)[1].strip()

        # Build prompt
        system_prompt = """あなたは Obsidian のタグ生成アシスタントです。
Markdown ファイルの内容に基づいて、3-5個の具体的なタグを生成してください。

ルール：
- フォルダ分類（エンジニア、ビジネス、経済、日常、その他）は含めない
- 具体的な技術名、製品名、トピック、キーワードのみ
- 日本語で出力
- 簡潔で検索可能なタグ

出力形式（JSON）:
{"tags": ["タグ1", "タグ2", "タグ3"]}"""

        user_message = f"""タイトル: {title}
要約: {summary}
内容プレビュー:
{body_preview}"""

        # Call Ollama
        response, error = call_ollama(system_prompt, user_message, timeout=30)

        if error:
            # Log error but don't fail the whole process
            return None

        # Parse JSON response
        try:
            data = json.loads(response)
            tags = data.get("tags", [])
            if isinstance(tags, list) and len(tags) > 0:
                return tags
        except json.JSONDecodeError:
            pass

        return None


class CleanContentStep(BaseStep):
    """Clean and format content."""

    @property
    def name(self) -> str:
        return "clean_content"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Clean and format content.

        Args:
            item: Item with content.

        Returns:
            Item with cleaned content.
        """
        content = item.transformed_content or item.content or ""

        # Remove excessive blank lines (more than 2 consecutive)
        content = re.sub(r"\n{3,}", "\n\n", content)

        # Ensure single newline at end
        content = content.rstrip() + "\n"

        item.transformed_content = content
        item.metadata["cleaned"] = True

        return item


class NormalizerTransformer(BaseStage):
    """Transform stage for Markdown normalization.

    Normalizes Markdown files to Obsidian format.
    """

    def __init__(self, steps: list[BaseStep] | None = None):
        """Initialize NormalizerTransformer.

        Args:
            steps: Optional custom steps. Defaults to standard normalization steps.
        """
        super().__init__()
        self._steps = steps or [
            ClassifyGenreStep(),
            NormalizeFrontmatterStep(),
            CleanContentStep(),
        ]

    @property
    def stage_type(self) -> StageType:
        return StageType.TRANSFORM

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps
