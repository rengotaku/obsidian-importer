"""
Stages - LLMパイプラインのステージ実装

処理ステージ（pre_process, stage_a, stage3_normalize, stage_c, post_process_v2）を実装。
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.models import (
    GenreType,
    ConfidenceLevel,
    PreProcessingResult,
    StageResult,
    Stage3Result,
    StageAResult,
    StageCResult,
    NormalizationResult,
    Frontmatter,
)
from normalizer.config import API_DELAY, VAULT_MAP, GENRES, get_genre_definitions_text
from normalizer.detection.english import is_complete_english_document
from normalizer.validators.title import validate_title
from normalizer.validators.tags import normalize_tags
from normalizer.validators.metadata import normalize_related, truncate_summary, normalize_created
from normalizer.io.ollama import parse_json_response
from normalizer.pipeline.prompts import load_prompt, call_llm_for_stage


# =============================================================================
# Template Markers
# =============================================================================

TEMPLATE_MARKERS = [
    "[TODO]",
    "[FIXME]",
    "Lorem ipsum",
    "PLACEHOLDER",
    "{{",
    "}}",
    "<%",
    "%>",
]


# =============================================================================
# Helper Functions
# =============================================================================


def extract_date_from_filename(filename: str) -> str:
    """ファイル名から日付を抽出（Jekyll形式対応）"""
    import re
    # パターン: 2022-10-17-Title.md or 2022_10_17_Title.md
    match = re.match(r'^(\d{4}[-_]\d{2}[-_]\d{2})[-_]', filename)
    if match:
        date_str = match.group(1).replace('_', '-')
        return date_str
    return ""


def _get_vault_subfolders() -> str:
    """各Vaultのサブフォルダ情報を取得してプロンプト用にフォーマット"""
    lines = []
    for genre, vault_path in VAULT_MAP.items():
        if genre == "dust":
            continue
        if not vault_path.exists():
            continue
        subfolders = []
        for item in vault_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                subfolders.append(item.name)
        if subfolders:
            subfolders.sort()
            lines.append(f"### {genre}")
            for sf in subfolders[:15]:  # 最大15個
                lines.append(f"- {sf}")
            lines.append("")
    return "\n".join(lines) if lines else "(サブフォルダ情報なし)"


# =============================================================================
# Pre-processing
# =============================================================================


def pre_process(filepath: Path, content: str) -> PreProcessingResult:
    """
    LLM呼び出し前のルールベース処理

    空ファイル、極短文、英語文書、テンプレート残骸を検出
    """
    stripped_content = content.strip()

    # 空ファイル判定
    is_empty = len(stripped_content) == 0

    # 極短文判定（50文字未満）
    is_too_short = len(stripped_content) < 50 and not is_empty

    # 英語文書判定
    is_english, english_score, _ = is_complete_english_document(content)

    # 日付抽出
    extracted_date = extract_date_from_filename(filepath.name)

    # テンプレート残骸検出
    has_template = any(marker.lower() in content.lower() for marker in TEMPLATE_MARKERS)

    # スキップ理由の決定
    skip_reason: str | None = None
    if is_empty:
        skip_reason = "空ファイル"
    elif is_too_short:
        skip_reason = f"極短文（{len(stripped_content)}文字）"
    elif has_template:
        skip_reason = "テンプレート残骸検出"

    return PreProcessingResult(
        is_empty=is_empty,
        is_too_short=is_too_short,
        is_english_doc=is_english,
        english_score=english_score,
        extracted_date=extracted_date,
        has_template_markers=has_template,
        skip_reason=skip_reason,
    )


# =============================================================================
# Stage A: Classification (Dust + Genre)
# =============================================================================

# Valid genres for Stage A (動的取得: config.GENRES)
VALID_GENRES = GENRES  # Vaults/ フォルダから動的に取得


def stage_a(content: str, filename: str, is_english: bool) -> StageResult:
    """
    Stage A - 分類判定（Dust判定 + ジャンル分類統合）

    1回のLLM呼び出しでdust判定とジャンル分類を同時実行
    """
    max_retries = 3
    retry_count = 0
    last_error: str | None = None
    raw_response: str | None = None

    try:
        system_prompt = load_prompt("stage_a_classify")
        # ジャンル定義を動的に挿入
        genre_definitions = get_genre_definitions_text()
        system_prompt = system_prompt.replace("{{GENRE_DEFINITIONS}}", genre_definitions)
        # サブフォルダ情報を挿入
        vault_subfolders = _get_vault_subfolders()
        system_prompt = system_prompt.replace("{{VAULT_SUBFOLDERS}}", vault_subfolders)
    except (FileNotFoundError, ValueError) as e:
        return StageResult(
            success=False,
            data=StageAResult(genre="その他", subfolder="", confidence="low", reason=str(e)),
            error=str(e),
            retry_count=0,
            raw_response=None,
        )

    truncated_content = content[:4000]
    extra_context = "言語: この文書は英語文書です" if is_english else ""

    while retry_count < max_retries:
        response, error = call_llm_for_stage(system_prompt, truncated_content, filename, extra_context)
        raw_response = response

        if error:
            last_error = error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        parsed, parse_error = parse_json_response(response)
        if parse_error:
            last_error = parse_error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        # フィールド検証
        genre = parsed.get("genre", "その他")
        if genre not in VALID_GENRES:
            genre = "その他"

        subfolder = parsed.get("subfolder", "")
        if not isinstance(subfolder, str):
            subfolder = ""
        # dustの場合はsubfolderを空にする
        if genre == "dust":
            subfolder = ""

        confidence_raw = parsed.get("confidence", "low")
        confidence: ConfidenceLevel = "high" if confidence_raw == "high" else "low"

        reason = parsed.get("reason", "判定理由なし")
        if not isinstance(reason, str):
            reason = str(reason)

        return StageResult(
            success=True,
            data=StageAResult(genre=genre, subfolder=subfolder, confidence=confidence, reason=reason),
            error=None,
            retry_count=retry_count,
            raw_response=raw_response,
        )

    return StageResult(
        success=False,
        data=StageAResult(genre="その他", subfolder="", confidence="low", reason=f"リトライ上限到達: {last_error}"),
        error=f"リトライ上限到達: {last_error}",
        retry_count=retry_count,
        raw_response=raw_response,
    )


# =============================================================================
# Stage B: Content Normalization (stage3_normalize)
# =============================================================================


def stage3_normalize(content: str, filename: str, genre: str, is_english: bool) -> StageResult:
    """
    Stage B (旧Stage 3) - コンテンツ正規化

    Markdown整形と改善
    """
    max_retries = 3
    retry_count = 0
    last_error: str | None = None
    raw_response: str | None = None

    try:
        system_prompt = load_prompt("stage3_normalize")
    except (FileNotFoundError, ValueError) as e:
        return StageResult(
            success=False,
            data=Stage3Result(normalized_content=content, improvements_made=[]),
            error=str(e),
            retry_count=0,
            raw_response=None,
        )

    # 追加コンテキスト
    extra_parts = [f"ジャンル: {genre}"]
    if is_english:
        extra_parts.append("【注意】この文書は英語文書です。翻訳せず、構造のみ整理してください。ただし、Summary/Conversation Overview セクションは日本語に翻訳してください。")
    extra_context = "\n".join(extra_parts)

    while retry_count < max_retries:
        response, error = call_llm_for_stage(system_prompt, content, filename, extra_context)
        raw_response = response

        if error:
            last_error = error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        parsed, parse_error = parse_json_response(response)
        if parse_error:
            last_error = parse_error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        normalized_content = parsed.get("normalized_content", "")
        improvements = parsed.get("improvements_made", [])

        # 空でないことを検証
        if not normalized_content or not normalized_content.strip():
            last_error = "normalized_contentが空です"
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        if not isinstance(improvements, list):
            improvements = []

        return StageResult(
            success=True,
            data=Stage3Result(normalized_content=normalized_content, improvements_made=improvements),
            error=None,
            retry_count=retry_count,
            raw_response=raw_response,
        )

    # リトライ失敗時は元のコンテンツを返す
    return StageResult(
        success=False,
        data=Stage3Result(normalized_content=content, improvements_made=[]),
        error=f"リトライ上限到達: {last_error}",
        retry_count=retry_count,
        raw_response=raw_response,
    )


# =============================================================================
# Stage C: Metadata Generation
# =============================================================================


def stage_c(normalized_content: str, filename: str, genre: str) -> StageResult:
    """
    Stage C - メタデータ生成（タイトル・タグ・サマリー・関連統合）

    1回のLLM呼び出しで4フィールドを同時生成
    """
    max_retries = 3
    retry_count = 0
    last_error: str | None = None
    raw_response: str | None = None

    try:
        system_prompt = load_prompt("stage_c_metadata")
    except (FileNotFoundError, ValueError) as e:
        stem = Path(filename).stem
        return StageResult(
            success=False,
            data=StageCResult(title=stem, tags=[], summary="", related=[]),
            error=str(e),
            retry_count=0,
            raw_response=None,
        )

    extra_context = f"ジャンル: {genre}"

    while retry_count < max_retries:
        response, error = call_llm_for_stage(system_prompt, normalized_content, filename, extra_context)
        raw_response = response

        if error:
            last_error = error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        parsed, parse_error = parse_json_response(response)
        if parse_error:
            last_error = parse_error
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        # タイトル検証
        title = parsed.get("title", "")
        is_valid, issues = validate_title(title)
        if not is_valid:
            last_error = f"タイトル検証失敗: {', '.join(issues)}"
            retry_count += 1
            time.sleep(API_DELAY)
            continue

        # タグ検証
        tags = parsed.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = tags[:5]  # 最大5個

        # サマリー検証（共通関数で正規化）
        summary = parsed.get("summary", "")
        if not isinstance(summary, str):
            summary = ""
        summary = truncate_summary(summary)

        # 関連ノート検証（共通関数で正規化）
        validated_related = normalize_related(parsed.get("related", []))

        # 作成日検証（共通関数で正規化）
        created = normalize_created(parsed.get("created", ""))

        return StageResult(
            success=True,
            data=StageCResult(
                title=title.strip(),
                tags=tags,
                summary=summary,
                related=validated_related,
                created=created,
            ),
            error=None,
            retry_count=retry_count,
            raw_response=raw_response,
        )

    # リトライ失敗時はファイル名から生成
    stem = Path(filename).stem
    return StageResult(
        success=False,
        data=StageCResult(title=stem, tags=[], summary="", related=[], created=""),
        error=f"リトライ上限到達: {last_error}",
        retry_count=retry_count,
        raw_response=raw_response,
    )


# =============================================================================
# Post-processing
# =============================================================================


def post_process_v2(
    pre_result: PreProcessingResult,
    stage_a_result: StageResult,
    stage_b_result: StageResult | None,
    stage_c_result: StageResult | None,
    filepath: Path,
) -> NormalizationResult:
    """
    新パイプライン（A→B→C）の結果を統合してNormalizationResultを生成

    - Stage A: 分類判定（genre, subfolder, confidence, reason）
    - Stage B: コンテンツ正規化（stage3_normalize）
    - Stage C: メタデータ生成（title, tags, summary, related）
    """
    # Stage結果からデータを抽出
    sa_data: StageAResult = stage_a_result["data"]
    sb_data: Stage3Result = stage_b_result["data"] if stage_b_result else {"normalized_content": "", "improvements_made": []}
    sc_data: StageCResult = stage_c_result["data"] if stage_c_result else {"title": filepath.stem, "tags": [], "summary": "", "related": [], "created": ""}

    # ジャンル・確信度
    genre: GenreType = sa_data.get("genre", "その他")
    confidence: ConfidenceLevel = sa_data.get("confidence", "low")
    reason = sa_data.get("reason", "")
    subfolder = sa_data.get("subfolder", "")

    # タグの正規化
    tags = normalize_tags(sc_data.get("tags", []))

    # 作成日: ファイル名から抽出 → LLM推測 の優先順位
    created = pre_result.get("extracted_date", "") or sc_data.get("created", "")

    # Frontmatter作成（新形式: summary, related追加）
    frontmatter = Frontmatter(
        title=sc_data.get("title", filepath.stem),
        tags=tags,
        created=created,
        summary=sc_data.get("summary", ""),
        related=sc_data.get("related", []),
        normalized=True,  # 内部フラグ（出力時は無視される）
    )

    return NormalizationResult(
        genre=genre,
        subfolder=subfolder,
        confidence=confidence,
        reason=reason,
        frontmatter=frontmatter,
        normalized_content=sb_data.get("normalized_content", ""),
        improvements_made=sb_data.get("improvements_made", []),
        is_complete_english_doc=pre_result.get("is_english_doc", False),
    )
