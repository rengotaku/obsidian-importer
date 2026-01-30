"""
エラーファイルのリトライ機能

Usage:
    python -m scripts.llm_import.cli --provider claude --retry-errors [--session SESSION_ID]

Functions:
    - find_session_dirs: セッションディレクトリを検索
    - load_errors_json: errors.json を読み込む
    - get_sessions_with_errors: エラーを含むセッション一覧を取得
    - validate_session: セッションの妥当性を検証
    - process_retry: リトライ処理を実行
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.llm_import.base import BaseConversation
    from scripts.llm_import.common.session_logger import SessionLogger


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SessionInfo:
    """セッション情報（リトライ用）"""

    session_id: str
    error_count: int
    updated_at: str
    source_session: str | None = None

    def __post_init__(self) -> None:
        """バリデーション"""
        if not self.session_id:
            raise ValueError("session_id は必須です")
        if self.error_count < 0:
            raise ValueError("error_count は 0 以上である必要があります")


@dataclass
class ErrorEntry:
    """エラーエントリ"""

    file: str
    error: str
    stage: str
    timestamp: str


# =============================================================================
# Session Discovery
# =============================================================================


def get_session_dir() -> Path:
    """@session ディレクトリのパスを取得"""
    # src/converter/scripts/llm_import/common/retry.py → src/converter/
    scripts_dir = Path(__file__).parent.parent.parent.parent
    project_root = scripts_dir.parent
    return project_root / ".staging" / "@session"


def find_session_dirs(session_base_dir: Path | None = None) -> list[Path]:
    """セッションディレクトリを検索

    Args:
        session_base_dir: @session ディレクトリのパス。None の場合はデフォルトを使用

    Returns:
        import セッションディレクトリのリスト（更新日時の降順）
        - 新構造: @session/import/YYYYMMDD_HHMMSS
        - 旧構造: @session/import_YYYYMMDD_HHMMSS（後方互換性）
    """
    if session_base_dir is None:
        session_base_dir = get_session_dir()

    if not session_base_dir.exists():
        return []

    session_dirs: list[Path] = []

    # 新構造: @session/import/ 配下のディレクトリ
    import_subdir = session_base_dir / "import"
    if import_subdir.exists() and import_subdir.is_dir():
        session_dirs.extend(
            d for d in import_subdir.iterdir() if d.is_dir()
        )

    # 旧構造: @session/import_* ディレクトリ（後方互換性）
    session_dirs.extend(
        d for d in session_base_dir.iterdir() if d.is_dir() and d.name.startswith("import_")
    )

    # 更新日時の降順でソート
    session_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)

    return session_dirs


def load_errors_json(session_dir: Path) -> list[ErrorEntry]:
    """errors.json を読み込む

    Args:
        session_dir: セッションディレクトリ

    Returns:
        ErrorEntry のリスト

    Raises:
        FileNotFoundError: errors.json が存在しない場合
        json.JSONDecodeError: JSON パースエラーの場合
    """
    errors_file = session_dir / "errors.json"

    if not errors_file.exists():
        raise FileNotFoundError(f"errors.json が見つかりません: {session_dir}")

    content = errors_file.read_text(encoding="utf-8")
    data = json.loads(content)

    return [
        ErrorEntry(
            file=entry.get("file", ""),
            error=entry.get("error", ""),
            stage=entry.get("stage", "unknown"),
            timestamp=entry.get("timestamp", ""),
        )
        for entry in data
    ]


def load_session_json(session_dir: Path) -> dict:
    """session.json を読み込む

    Args:
        session_dir: セッションディレクトリ

    Returns:
        セッション情報の辞書

    Raises:
        FileNotFoundError: session.json が存在しない場合
    """
    session_file = session_dir / "session.json"

    if not session_file.exists():
        raise FileNotFoundError(f"session.json が見つかりません: {session_dir}")

    content = session_file.read_text(encoding="utf-8")
    return json.loads(content)


def get_sessions_with_errors(session_base_dir: Path | None = None) -> list[SessionInfo]:
    """エラーを含むセッション一覧を取得

    Args:
        session_base_dir: @session ディレクトリのパス

    Returns:
        エラーを含む SessionInfo のリスト（更新日時の降順）
    """
    session_dirs = find_session_dirs(session_base_dir)
    sessions: list[SessionInfo] = []

    for session_dir in session_dirs:
        errors_file = session_dir / "errors.json"
        if not errors_file.exists():
            continue

        try:
            errors = load_errors_json(session_dir)
            if not errors:
                continue

            # session.json から追加情報を取得
            session_data = {}
            try:
                session_data = load_session_json(session_dir)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            # 更新日時を取得
            updated_at = session_data.get("updated_at", "")
            if not updated_at:
                # ファイルの更新日時をフォールバック
                mtime = errors_file.stat().st_mtime
                updated_at = datetime.fromtimestamp(mtime).isoformat()

            sessions.append(
                SessionInfo(
                    session_id=session_dir.name,
                    error_count=len(errors),
                    updated_at=updated_at,
                    source_session=session_data.get("source_session"),
                )
            )
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    return sessions


# =============================================================================
# Validation
# =============================================================================


def validate_session(session_id: str, session_base_dir: Path | None = None) -> tuple[bool, str]:
    """セッションの妥当性を検証

    Args:
        session_id: セッション ID
        session_base_dir: @session ディレクトリのパス

    Returns:
        (valid, message) のタプル
    """
    if session_base_dir is None:
        session_base_dir = get_session_dir()

    session_dir = session_base_dir / session_id

    if not session_dir.exists():
        return False, f"セッション '{session_id}' が見つかりません"

    if not session_dir.is_dir():
        return False, f"'{session_id}' はディレクトリではありません"

    errors_file = session_dir / "errors.json"
    if not errors_file.exists():
        return False, f"セッション '{session_id}' にエラーファイルがありません"

    try:
        errors = load_errors_json(session_dir)
        if not errors:
            return False, f"セッション '{session_id}' にエラーがありません"
    except json.JSONDecodeError as e:
        return False, f"errors.json の読み込みエラー: {e}"

    return True, f"リトライ対象: {len(errors)} 件"


# =============================================================================
# Conversation Data Access
# =============================================================================


def get_llm_exports_base() -> Path:
    """LLM エクスポート格納先を取得"""
    scripts_dir = Path(__file__).parent.parent.parent.parent
    project_root = scripts_dir.parent
    return project_root / ".staging" / "@llm_exports"


def find_conversations_json(provider: str = "claude") -> Path | None:
    """conversations.json のパスを検索

    Args:
        provider: プロバイダー名

    Returns:
        conversations.json のパス、または None
    """
    base_dir = get_llm_exports_base() / provider

    if not base_dir.exists():
        return None

    # サブディレクトリ内の conversations.json を探す
    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            candidate = subdir / "conversations.json"
            if candidate.exists():
                return candidate

    return None


def load_conversation_by_id(
    conversation_id: str, provider: str = "claude"
) -> "BaseConversation | None":
    """会話 ID から会話データを取得

    Args:
        conversation_id: 会話 ID (UUID)
        provider: プロバイダー名

    Returns:
        会話データ、または None
    """
    from scripts.llm_import.providers import PROVIDERS

    conversations_json = find_conversations_json(provider)
    if not conversations_json:
        return None

    # パーサーを取得してパース
    parser_class = PROVIDERS.get(provider)
    if not parser_class:
        return None

    parser = parser_class()
    try:
        conversations = parser.parse(conversations_json.parent)

        # ID で検索
        for conv in conversations:
            if conv.id == conversation_id:
                return conv
    except Exception:
        pass

    return None


# =============================================================================
# Retry Processing
# =============================================================================


def process_retry(
    session_id: str,
    provider: str,
    output_dir: Path,
    timeout: int = 120,
    verbose: bool = False,
    session_logger: "SessionLogger | None" = None,
) -> tuple[int, int]:
    """リトライ処理を実行

    Args:
        session_id: リトライ元セッション ID
        provider: プロバイダー名
        output_dir: 出力ディレクトリ
        timeout: タイムアウト秒数
        verbose: 詳細ログ出力
        session_logger: SessionLogger インスタンス

    Returns:
        (success_count, error_count) のタプル
    """
    from scripts.llm_import.common.knowledge_extractor import KnowledgeExtractor
    from scripts.llm_import.base import sanitize_filename

    session_base_dir = get_session_dir()
    session_dir = session_base_dir / session_id

    # エラーを読み込む
    errors = load_errors_json(session_dir)

    if not errors:
        print("✅ リトライ対象のエラーがありません")
        return 0, 0

    # 知識抽出器
    # Note: timeout is not currently supported by KnowledgeExtractor
    extractor = KnowledgeExtractor()

    success_count = 0
    error_count = 0
    total = len(errors)

    for i, entry in enumerate(errors, 1):
        conversation_id = entry.file
        print(f"[{i}/{total}] Processing {conversation_id}...")

        # 元の会話データを取得
        conversation = load_conversation_by_id(conversation_id, provider)

        if not conversation:
            msg = f"会話データが見つかりません: {conversation_id}"
            print(f"  ❌ {msg}")
            if session_logger:
                session_logger.add_error(
                    file=conversation_id, error=msg, stage="phase1"
                )
            error_count += 1
            continue

        # Phase 2: 知識抽出をリトライ
        try:
            result = extractor.extract(conversation)

            if not result.success:
                print(f"  ❌ Error: {result.error}")
                if session_logger:
                    session_logger.add_error(
                        file=conversation_id,
                        error=result.error or "Unknown error",
                        stage="phase2",
                    )
                error_count += 1
                continue

            # 出力ファイルを作成
            document = result.document
            output_filename = sanitize_filename(document.title) + ".md"
            output_path = output_dir / output_filename

            output_path.write_text(document.to_markdown(), encoding="utf-8")

            print(f"  ✅ Success → {output_path.name}")
            if session_logger:
                session_logger.add_processed(
                    file=conversation_id, output=str(output_path)
                )
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            if session_logger:
                session_logger.add_error(
                    file=conversation_id, error=str(e), stage="phase2"
                )
            error_count += 1

    return success_count, error_count


# =============================================================================
# Session Selection
# =============================================================================


def format_session_list(sessions: list[SessionInfo]) -> str:
    """セッション一覧をフォーマット

    Args:
        sessions: SessionInfo のリスト

    Returns:
        フォーマットされた文字列
    """
    if not sessions:
        return "リトライ対象のセッションがありません"

    lines = [
        "リトライ対象のセッション一覧:",
        "",
        "  SESSION                      ERRORS  UPDATED",
    ]

    for session in sessions:
        # updated_at から日付部分を抽出
        updated_display = session.updated_at[:16].replace("T", " ")
        lines.append(
            f"  {session.session_id:<28} {session.error_count:<7} {updated_display}"
        )

    lines.extend(
        [
            "",
            "SESSION を指定して実行してください:",
            "  python -m scripts.llm_import.cli --provider claude --retry-errors --session <SESSION_ID>",
        ]
    )

    return "\n".join(lines)


def select_session_interactive(
    sessions: list[SessionInfo],
) -> SessionInfo | None:
    """セッションを自動選択（1件のみの場合）

    Args:
        sessions: SessionInfo のリスト

    Returns:
        1件のみなら自動選択、複数なら None
    """
    if len(sessions) == 1:
        return sessions[0]
    return None


# =============================================================================
# Preview Mode
# =============================================================================


def format_error_preview(errors: list[ErrorEntry]) -> str:
    """エラー一覧をプレビュー用にフォーマット

    Args:
        errors: ErrorEntry のリスト

    Returns:
        フォーマットされた文字列
    """
    if not errors:
        return "リトライ対象のエラーがありません"

    lines = [
        "リトライ対象のエラー一覧:",
        "",
        "  FILE                                   ERROR                          TIMESTAMP",
    ]

    for entry in errors:
        # UUIDの最初の部分とエラーメッセージを切り詰め
        file_display = entry.file[:36]
        error_display = entry.error[:30] + ("..." if len(entry.error) > 30 else "")
        timestamp_display = entry.timestamp[:16].replace("T", " ")
        lines.append(f"  {file_display:<40} {error_display:<30} {timestamp_display}")

    lines.extend(
        [
            "",
            f"合計: {len(errors)} 件",
            "",
            "[プレビューモード] 実際の処理は行われません",
        ]
    )

    return "\n".join(lines)


def preview_retry(session_id: str, session_base_dir: Path | None = None) -> str:
    """リトライ対象をプレビュー

    Args:
        session_id: セッション ID
        session_base_dir: @session ディレクトリのパス

    Returns:
        プレビュー文字列
    """
    if session_base_dir is None:
        session_base_dir = get_session_dir()

    session_dir = session_base_dir / session_id

    try:
        errors = load_errors_json(session_dir)
        return format_error_preview(errors)
    except FileNotFoundError as e:
        return f"❌ {e}"
    except json.JSONDecodeError as e:
        return f"❌ errors.json の読み込みエラー: {e}"
