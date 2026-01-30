"""
State Manager - 処理状態管理

処理状態の保存・読み込み・更新を行う。
グローバル状態を StateManager シングルトンで管理。
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from normalizer.models import ProcessingResult

from normalizer.io.session import (
    load_latest_session,
    get_state_files,
    timestamp,
)


# =============================================================================
# State Manager Singleton
# =============================================================================


class StateManager:
    """グローバル状態を管理するシングルトン"""

    _instance: ClassVar["StateManager | None"] = None

    def __new__(cls) -> "StateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """状態の初期化"""
        self.session_dir: Path | None = None
        self.cached_prompt: str | None = None
        self.stage_debug_mode: bool = False
        self.excluded_files: list[tuple[Path, str]] = []

    def reset(self) -> None:
        """テスト用: 状態をリセット"""
        self._initialize()

    def set_session_dir(self, session_dir: Path | None) -> None:
        """セッションディレクトリを設定"""
        self.session_dir = session_dir


def get_state() -> StateManager:
    """StateManager インスタンスを取得"""
    return StateManager()


# =============================================================================
# State Persistence
# =============================================================================


def load_state() -> dict | None:
    """処理状態を読み込み（最新セッションから、分割ファイル版）"""
    state_mgr = get_state()
    session = load_latest_session()
    if session is None:
        return None

    state_mgr.set_session_dir(session)
    files = get_state_files(session)

    # session.json が存在しなければ状態なし
    if not files["session"].exists():
        return None

    try:
        # 各ファイルから読み込み
        session_data = json.loads(files["session"].read_text(encoding="utf-8"))
        pending = json.loads(files["pending"].read_text(encoding="utf-8")) if files["pending"].exists() else []
        processed = json.loads(files["processed"].read_text(encoding="utf-8")) if files["processed"].exists() else []
        errors = json.loads(files["errors"].read_text(encoding="utf-8")) if files["errors"].exists() else []

        return {
            **session_data,
            "pending": pending,
            "processed": processed,
            "errors": errors,
        }
    except Exception:
        return None


def save_state(state: dict) -> None:
    """処理状態を保存（分割ファイル版）"""
    state_mgr = get_state()
    if state_mgr.session_dir is None:
        raise RuntimeError("セッションが開始されていません")

    # ディレクトリが存在しない場合は作成（防御的プログラミング）
    if not state_mgr.session_dir.exists():
        state_mgr.session_dir.mkdir(parents=True, exist_ok=True)

    files = get_state_files(state_mgr.session_dir)

    # session.json - メタデータのみ
    session_data = {
        "session_id": state.get("session_id"),
        "started_at": state.get("started_at"),
        "updated_at": state.get("updated_at"),
        "total_files": state.get("total_files"),
    }
    files["session"].write_text(
        json.dumps(session_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # pending.json - 未処理ファイルリスト
    files["pending"].write_text(
        json.dumps(state.get("pending", []), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # processed.json - 処理済みファイルリスト
    files["processed"].write_text(
        json.dumps(state.get("processed", []), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # errors.json - エラーファイルリスト
    files["errors"].write_text(
        json.dumps(state.get("errors", []), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def delete_state() -> None:
    """処理状態を削除（最新のセッションディレクトリを削除）"""
    state_mgr = get_state()

    # 現在のセッションディレクトリがあればそれを削除
    session_to_delete = state_mgr.session_dir

    # なければ最新のセッションを探す
    if session_to_delete is None:
        session_to_delete = load_latest_session()

    if session_to_delete and session_to_delete.exists():
        shutil.rmtree(session_to_delete)

    state_mgr.session_dir = None


def create_initial_state(files: list[Path]) -> dict:
    """初期状態を作成"""
    return {
        "session_id": timestamp(),
        "started_at": timestamp(),
        "updated_at": timestamp(),
        "total_files": len(files),
        "processed": [],
        "pending": [f.name for f in files],
        "errors": []
    }


def update_state(state: dict, result: "ProcessingResult") -> dict:
    """処理結果で状態を更新"""
    state["updated_at"] = timestamp()

    # processed エントリ作成（file_id を含む）
    processed_entry = {
        "file": result["file"],
        "status": "success" if result["success"] else "error",
        "destination": result["destination"],
        "timestamp": result["timestamp"]
    }
    # file_id が存在する場合のみ追加（後方互換性）
    if result.get("file_id"):
        processed_entry["file_id"] = result["file_id"]

    state["processed"].append(processed_entry)

    # pending はファイル名のみ、result["file"] はパスの場合があるため basename で比較
    filename = Path(result["file"]).name if "/" in str(result["file"]) else result["file"]
    if filename in state["pending"]:
        state["pending"].remove(filename)

    # errors エントリ作成（file_id を含む）
    if not result["success"] and result["error"]:
        error_entry = {
            "file": result["file"],
            "error": result["error"],
            "timestamp": result["timestamp"]
        }
        # file_id が存在する場合のみ追加（後方互換性）
        if result.get("file_id"):
            error_entry["file_id"] = result["file_id"]

        state["errors"].append(error_entry)

    return state
