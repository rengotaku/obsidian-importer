"""
Status Command - 処理状態表示コマンド

現在の処理状態、フォルダ統計、セッション情報を表示。
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.config import (
    INDEX_DIR,
    DUST_DIR,
    SESSION_DIR,
)
from normalizer.state.manager import load_state
from normalizer.io.files import (
    list_index_files,
    get_excluded_files,
    clear_excluded_files,
)
from normalizer.io.session import get_session_dir


def cmd_status(output_json: bool = False, verbose: bool = False) -> int:
    """処理状態を表示"""
    clear_excluded_files()

    # フォルダ統計
    index_files = list_index_files() if INDEX_DIR.exists() else []
    dust_files = list(DUST_DIR.glob("*.md")) if DUST_DIR.exists() else []

    # 直下/サブフォルダ別カウント
    direct_files = [f for f in index_files if f.parent == INDEX_DIR]
    subfolder_files = [f for f in index_files if f.parent != INDEX_DIR]

    # JSON出力用データ構造
    status_data = {
        "folders": {
            "index": {
                "path": str(INDEX_DIR),
                "count": len(index_files),
                "direct_count": len(direct_files),
                "subfolder_count": len(subfolder_files),
                "files": [str(f.relative_to(INDEX_DIR)) for f in index_files]
            },
            "dust": {
                "path": str(DUST_DIR),
                "count": len(dust_files),
                "files": [f.name for f in dust_files]
            }
        },
        "session": None,
        "past_sessions": []
    }

    state = load_state()
    if state:
        session_dir = get_session_dir()
        status_data["session"] = {
            "name": session_dir.name if session_dir else "unknown",
            "started_at": state["started_at"],
            "updated_at": state["updated_at"],
            "total_files": state["total_files"],
            "processed_count": len(state["processed"]),
            "pending_count": len(state["pending"]),
            "error_count": len(state["errors"]),
            "pending_files": state["pending"][:20],
            "errors": state["errors"][:10]
        }

    # 過去のセッション一覧（test_ プレフィックスは除外）
    if SESSION_DIR.exists():
        sessions = sorted(
            [d.name for d in SESSION_DIR.iterdir() if d.is_dir() and not d.name.startswith("test_")],
            reverse=True
        )
        status_data["past_sessions"] = sessions[:10]

    # 除外ファイル情報
    excluded = get_excluded_files()
    status_data["excluded"] = {
        "count": len(excluded),
        "files": [{"path": str(p.relative_to(INDEX_DIR)), "reason": r} for p, r in excluded[:50]] if verbose else []
    }

    # JSON出力
    if output_json:
        print(json.dumps(status_data, ensure_ascii=False, indent=2))
        return 0

    # テキスト出力
    _print_folder_stats(index_files, direct_files, subfolder_files, dust_files, excluded)
    _print_excluded_files(verbose, excluded)
    _print_session_state(state, status_data)

    return 0


def _print_folder_stats(
    index_files: list,
    direct_files: list,
    subfolder_files: list,
    dust_files: list,
    excluded: list
) -> None:
    """フォルダ統計を表示"""
    print(f"\n{'='*60}")
    print("  📊 フォルダ統計")
    print(f"{'='*60}")
    print(f"  📥 @index (未処理): {len(index_files)} ファイル")
    print(f"      ├─ 直下: {len(direct_files)} ファイル")
    print(f"      └─ サブフォルダ: {len(subfolder_files)} ファイル")
    if excluded:
        print(f"      (除外: {len(excluded)} ファイル)")
    print(f"  🗑️ @dust: {len(dust_files)} ファイル")


def _print_excluded_files(verbose: bool, excluded: list) -> None:
    """除外ファイル一覧表示"""
    if not verbose or not excluded:
        return

    print(f"\n🚫 除外されたファイル ({len(excluded)} 件):")
    folders: dict[str, list[str]] = {}
    for path, reason in excluded:
        try:
            rel = path.relative_to(INDEX_DIR)
            folder = rel.parts[0] if len(rel.parts) > 1 else "(ルート)"
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(f"{rel.name} ({reason})")
        except ValueError:
            pass

    for folder, files in sorted(folders.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"   📁 {folder}: {len(files)} ファイル")
        for f in files[:3]:
            print(f"      - {f}")
        if len(files) > 3:
            print(f"      ... 他 {len(files) - 3} ファイル")
    if len(folders) > 10:
        print(f"   ... 他 {len(folders) - 10} フォルダ")


def _print_session_state(state: dict | None, status_data: dict) -> None:
    """セッション状態を表示"""
    if not state:
        print(f"\n{'='*60}")
        print("📋 処理状態: なし（新規セッション開始可能）")
        if status_data["past_sessions"]:
            print(f"\n📁 過去のセッション ({len(status_data['past_sessions'])} 件):")
            for s in status_data["past_sessions"][:5]:
                print(f"    - {s}")
            if len(status_data["past_sessions"]) > 5:
                print(f"    ... 他 {len(status_data['past_sessions']) - 5} セッション")
        print(f"{'='*60}")
        return

    session_dir = get_session_dir()
    print(f"\n{'='*60}")
    print("📋 セッション状態:")
    print(f"  セッション: {session_dir.name if session_dir else 'unknown'}")
    print(f"  開始時刻: {state['started_at']}")
    print(f"  最終更新: {state['updated_at']}")
    print(f"  総ファイル数: {state['total_files']}")
    print(f"  処理済み: {len(state['processed'])}")
    print(f"  残り: {len(state['pending'])}")
    print(f"  エラー: {len(state['errors'])}")

    if state["pending"]:
        print("\n⏳ 未処理ファイル:")
        for f in state["pending"][:5]:
            print(f"    - {f}")
        if len(state["pending"]) > 5:
            print(f"    ... 他 {len(state['pending']) - 5} ファイル")

    print(f"{'='*60}")
