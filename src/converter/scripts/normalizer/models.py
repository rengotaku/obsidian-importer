"""
Types - TypedDict、型定義

全ての型定義を集約し、循環インポートを防ぐ。
他のモジュールはこのモジュールから型をインポートする。
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict, Literal

# =============================================================================
# Genre Type
# =============================================================================

# GenreType は動的（Vaults/ フォルダから取得）のため str を使用
# 有効なジャンルは normalizer.config.GENRES で定義
GenreType = str
ConfidenceLevel = Literal["high", "low"]

# =============================================================================
# Pre-processing Types
# =============================================================================


class PreProcessingResult(TypedDict):
    """LLM呼び出し前のルールベース処理結果"""
    is_empty: bool              # 空ファイル
    is_too_short: bool          # 50文字未満
    is_english_doc: bool        # 完全な英語文書
    english_score: float        # 英語判定スコア (0.0-1.0)
    extracted_date: str         # ファイル名から抽出した日付 (YYYY-MM-DD or "")
    has_template_markers: bool  # テンプレート残骸検出
    skip_reason: str | None     # スキップする場合の理由


# =============================================================================
# Stage Result Types
# =============================================================================


class StageResult(TypedDict):
    """各LLM処理段階の結果を表す汎用型"""
    success: bool               # 処理成功
    data: dict                  # 段階固有の出力データ
    error: str | None           # エラーメッセージ
    retry_count: int            # リトライ回数
    raw_response: str | None    # LLMの生応答（デバッグ用）


class Stage1Result(TypedDict):
    """Stage 1: Dust判定結果 (旧形式 - Phase 5で削除予定)"""
    is_dust: bool
    dust_reason: str | None
    confidence: float           # 0.0-1.0


class Stage2Result(TypedDict):
    """Stage 2: ジャンル分類結果 (旧形式 - Phase 5で削除予定)"""
    genre: GenreType
    subfolder: str              # サブフォルダ名（空文字=ルート、"新規: xxx"=新規作成）
    confidence: float           # 0.0-1.0
    related_keywords: list[str]  # 3-5個


# =============================================================================
# New Stage Types (Pipeline統合用)
# =============================================================================


class StageAResult(TypedDict):
    """Stage A: 分類判定結果（Dust判定 + ジャンル分類統合）"""
    genre: GenreType            # Vaults/ 配下のフォルダ名 または "dust"
    subfolder: str              # サブフォルダ名（空文字=ルート、"新規: xxx"=新規作成）
    confidence: ConfidenceLevel  # "high" or "low"
    reason: str                 # 判定理由


class StageCResult(TypedDict):
    """Stage C: メタデータ生成結果（タイトル・タグ・サマリー・関連・作成日統合）"""
    title: str                  # ファイル名に使用可能なタイトル
    tags: list[str]             # 3-5個のタグ
    summary: str                # 最大200文字のサマリー
    related: list[str]          # 内部リンク形式 [["ファイル名"]]、最大5件
    created: str                # 作成日（YYYY-MM-DD）、推測不可の場合は空文字


class Stage3Result(TypedDict):
    """Stage 3: コンテンツ正規化結果"""
    normalized_content: str     # 整形済み本文
    improvements_made: list[str]  # 改善リスト


class Stage4Result(TypedDict):
    """Stage 4: タイトル・タグ生成結果"""
    title: str                  # ファイル名に使用可能なタイトル
    tags: list[str]             # 3-5個のタグ


class Stage5Result(TypedDict):
    """Stage 5: Summary品質改善結果"""
    improved_summary: str       # 改善されたSummaryセクション
    changes_made: list[str]     # 改善内容リスト


# =============================================================================
# Pipeline Types
# =============================================================================


class PipelineContext(TypedDict):
    """処理パイプライン全体のコンテキスト"""
    filepath: Path              # 処理対象ファイル
    original_content: str       # 元のファイル内容
    pre_result: PreProcessingResult
    stage1_result: StageResult | None
    stage2_result: StageResult | None
    stage3_result: StageResult | None
    stage4_result: StageResult | None
    final_result: "NormalizationResult | None"  # Forward reference
    errors: list[str]           # 累積エラー
    processing_time_ms: int     # 処理時間


# =============================================================================
# Output Types
# =============================================================================


class Frontmatter(TypedDict):
    """YAML Frontmatter"""
    title: str
    tags: list[str]
    created: str
    # Pipeline統合: 新規追加フィールド
    summary: str                # サマリー（最大200文字）
    related: list[str]          # 関連ノート [["ファイル名"]]形式
    normalized: bool            # 正規化済みフラグ（常にTrue）


class NormalizationResult(TypedDict):
    """正規化処理の最終結果"""
    genre: GenreType
    subfolder: str              # サブフォルダ名（空文字=ルート）
    confidence: ConfidenceLevel  # "high" or "low"
    reason: str                 # 判定理由
    frontmatter: Frontmatter
    normalized_content: str
    # Phase 6: US4 追加フィールド
    improvements_made: list[str]
    is_complete_english_doc: bool


class ProcessingResult(TypedDict):
    """単一ファイル処理結果"""
    success: bool
    file: str
    genre: GenreType | None
    confidence: ConfidenceLevel
    destination: str | None
    error: str | None
    timestamp: str
    # 文字数統計（Phase 5追加）
    original_chars: int | None
    normalized_chars: int | None
    char_diff: int | None
    # Phase 6: US4 追加フィールド
    improvements_made: list[str] | None
    is_complete_english_doc: bool | None
    # 019: ファイル追跡ハッシュID
    file_id: str | None


class ScanResult(TypedDict):
    """@index/以下のスキャン結果を表す型定義"""
    total_files: int       # 検出されたファイル総数
    direct_files: int      # @index/ 直下のファイル数
    subfolder_files: int   # サブフォルダ内のファイル数
    excluded_count: int    # 除外されたファイル数
    files: list[Path]      # 処理対象ファイルリスト
