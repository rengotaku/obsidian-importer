"""
Session Management - セッション管理

セッションディレクトリの作成・読み込み・ログ記録を行う。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import SESSION_DIR


# =============================================================================
# Utility Functions
# =============================================================================


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """プログレスバーを生成"""
    if total == 0:
        return "[" + "░" * width + "] 0/0 (0%)"
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({percent*100:.1f}%)"


def timestamp() -> str:
    """現在時刻をISO形式で返す"""
    return datetime.now().isoformat(timespec="seconds")


# =============================================================================
# Session Management
# =============================================================================


def get_session_dir() -> Path | None:
    """現在のセッションディレクトリを取得

    StateManagerのsession_dirを返す。

    Returns:
        セッションディレクトリ、または None
    """
    from normalizer.state.manager import get_state
    state_mgr = get_state()
    return state_mgr.session_dir


def get_state_files(session_dir: Path) -> dict[str, Path]:
    """状態ファイルのパスを取得（分割版）"""
    return {
        "session": session_dir / "session.json",
        "pending": session_dir / "pending.json",
        "processed": session_dir / "processed.json",
        "errors": session_dir / "errors.json",
    }


def get_log_file(session_dir: Path) -> Path:
    """ログファイルのパスを取得"""
    return session_dir / "execution.log"


def create_new_session(prefix: str = "organize") -> Path:
    """新しいセッションディレクトリを作成

    Args:
        prefix: サブディレクトリ名（デフォルト: "organize"）

    Returns:
        作成されたセッションディレクトリのパス

    Examples:
        create_new_session()            -> .staging/@session/organize/20260116_185500/
        create_new_session("organize")  -> .staging/@session/organize/20260116_185500/
        create_new_session("test")      -> .staging/@session/test/20260116_185500/
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = SESSION_DIR / prefix / timestamp_str
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def load_latest_session() -> Path | None:
    """最新のセッションディレクトリを読み込み

    @session/organize/ 配下から最新のセッションを取得。
    test/ サブディレクトリは無視する（テスト用）。

    Returns:
        最新のセッションディレクトリ、存在しない場合はNone
    """
    organize_dir = SESSION_DIR / "organize"
    if not organize_dir.exists():
        return None
    sessions = sorted(
        [d for d in organize_dir.iterdir() if d.is_dir()],
        reverse=True
    )
    if sessions:
        return sessions[0]
    return None


def log_message(
    message: str,
    session_dir: Path | None = None,
    also_print: bool = True
) -> None:
    """ログファイルにメッセージを追記

    Args:
        message: ログメッセージ
        session_dir: セッションディレクトリ（省略時は自動取得）
        also_print: コンソールにも出力するか
    """
    # session_dir 未指定時は自動取得
    if session_dir is None:
        session_dir = get_session_dir()

    # セッションがない場合はprintのみ
    if session_dir is None:
        if also_print:
            print(message)
        return

    log_file = get_log_file(session_dir)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp()}] {message}\n")
    if also_print:
        print(message)


def start_new_log_session() -> Path:
    """新しいログセッションを開始

    StateManager にも自動的にセッションディレクトリを設定する。

    Returns:
        作成されたセッションディレクトリのパス
    """
    from normalizer.state.manager import get_state

    session_dir = create_new_session()

    # StateManager に自動設定
    state_mgr = get_state()
    state_mgr.set_session_dir(session_dir)

    log_file = get_log_file(session_dir)
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"{'='*60}\n")
        f.write(f"セッション: {session_dir.name}\n")
        f.write(f"開始時刻: {timestamp()}\n")
        f.write(f"{'='*60}\n\n")
    return session_dir
