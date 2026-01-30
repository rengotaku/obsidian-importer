"""
Batch - バッチ処理

複数ファイルの一括処理とサマリー表示を行う。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.models import ProcessingResult
from normalizer.config import API_DELAY, VAULT_MAP, BASE_DIR
from normalizer.state.manager import (
    get_state,
    create_initial_state,
    update_state,
    save_state,
)
from normalizer.io.session import progress_bar, log_message
from normalizer.processing.single import process_single_file


# =============================================================================
# Batch Processing
# =============================================================================


def process_all_files(
    files: list[Path],
    preview: bool = False,
    quiet: bool = False,
    output_json: bool = False,
    state: dict | None = None
) -> dict:
    """複数ファイルを一括処理

    Args:
        files: 処理対象ファイルリスト
        preview: プレビューモード
        quiet: 進捗表示抑制
        output_json: JSON出力
        state: 既存の状態（再開用）

    Returns:
        処理結果サマリー
    """
    state_mgr = get_state()

    # 状態初期化
    if state is None:
        state = create_initial_state(files)
        save_state(state)

    # 処理済みファイルを除外
    pending_names = set(state["pending"])
    files_to_process = [f for f in files if f.name in pending_names]

    # 統計
    stats = {
        "success": 0,
        "dust": 0,
        "error": 0
    }
    results: list[ProcessingResult] = []

    total = len(files_to_process)
    if not quiet and not output_json:
        log_message(f"\n{'='*60}")
        log_message(f"  処理開始: {total} ファイル")
        log_message(f"{'='*60}\n")

    for i, filepath in enumerate(files_to_process, 1):
        # 進捗表示（コンソールのみ）
        if not quiet and not output_json:
            sys.stdout.write(f"\r{progress_bar(i, total)} {filepath.name[:30]}")
            sys.stdout.flush()

        # ファイル処理
        result = process_single_file(
            filepath,
            preview=preview,
            quiet=True,
            output_json=False
        )
        results.append(result)

        # 統計更新
        if result["success"]:
            if result["genre"] == "dust":
                stats["dust"] += 1
            else:
                stats["success"] += 1
        else:
            stats["error"] += 1

        # 状態更新
        state = update_state(state, result)
        save_state(state)

        # API負荷軽減
        time.sleep(API_DELAY)

    # 改行
    if not quiet and not output_json:
        print()

    # 処理完了時もセッションフォルダは保持（履歴・ログ参照用）
    # pending が空でも削除しない

    # 結果サマリー
    summary = {
        "total": total,
        "stats": stats,
        "results": results
    }

    # JSON結果をセッションディレクトリに保存
    session_dir = state_mgr.session_dir
    if session_dir:
        result_file = session_dir / "results.json"
        result_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )

    # 出力
    if output_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    elif not quiet:
        print_summary(stats, results, preview)

    return summary


# =============================================================================
# Summary Display
# =============================================================================


def print_summary(stats: dict, results: list[ProcessingResult], preview: bool = False) -> None:
    """処理結果サマリーを表示"""
    log_message(f"\n{'='*60}")
    log_message("  📊 処理結果サマリー")
    log_message(f"{'='*60}")

    mode_label = "（プレビュー）" if preview else ""
    log_message(f"  ✅ 成功{mode_label}: {stats['success']} ファイル")
    log_message(f"  🗑️ Dust: {stats['dust']} ファイル")
    log_message(f"  ❌ エラー: {stats['error']} ファイル")

    # 移動先Vault別カウント
    vault_counts: dict[str, int] = {}
    for r in results:
        if r["success"] and r["genre"] and r["genre"] != "dust":
            genre = r["genre"]
            vault_counts[genre] = vault_counts.get(genre, 0) + 1
    if vault_counts:
        log_message(f"\n📂 移動先Vault別:")
        for genre, count in sorted(vault_counts.items(), key=lambda x: -x[1]):
            vault_path = VAULT_MAP.get(genre, BASE_DIR / "その他")
            log_message(f"    {genre}: {count} ファイル → {vault_path.name}/")

    # 成功したファイルの詳細
    success_results = [r for r in results if r["success"] and r["genre"] != "dust"]
    if success_results:
        log_message(f"\n📁 移動{'予定' if preview else '済み'}ファイル:")
        for r in success_results[:10]:
            log_message(f"  {Path(r['file']).name} → {r['destination']}")
        if len(success_results) > 10:
            log_message(f"  ... 他 {len(success_results) - 10} ファイル")

    # dustファイルの詳細
    dust_results = [r for r in results if r["genre"] == "dust"]
    if dust_results:
        log_message(f"\n🗑️ Dust判定ファイル:")
        for r in dust_results[:5]:
            log_message(f"  {Path(r['file']).name}")
        if len(dust_results) > 5:
            log_message(f"  ... 他 {len(dust_results) - 5} ファイル")

    # エラーファイルの詳細
    error_results = [r for r in results if not r["success"] and r["error"]]
    if error_results:
        log_message(f"\n❌ エラー発生ファイル:")
        for r in error_results:
            log_message(f"  {Path(r['file']).name}: {r['error']}")

    log_message(f"\n{'='*60}")
