"""
Metrics Command - 品質メトリクス表示コマンド

セッションの品質メトリクス（タイトル、タグ、フォーマット、英語判定）を表示。
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from normalizer.io.session import load_latest_session


def cmd_metrics(output_json: bool = False) -> int:
    """品質メトリクスを表示"""
    session = load_latest_session()
    if session is None:
        print("📊 品質メトリクス: セッションがありません")
        return 0

    metrics = {
        "session": session.name,
        "title": {"total": 0, "valid": 0, "rate": 0.0, "issues": []},
        "tags": {"total": 0, "avg_consistency": 0.0, "matched": 0, "unmatched": 0},
        "format": {"total": 0, "valid": 0, "rate": 0.0, "common_issues": {}},
        "english": {"total": 0, "detected": 0, "avg_score": 0.0}
    }

    _load_title_metrics(session, metrics)
    _load_tag_metrics(session, metrics)
    _load_format_metrics(session, metrics)
    _load_english_metrics(session, metrics)

    # 出力
    if output_json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0

    _print_metrics(metrics)
    return 0


def _load_title_metrics(session, metrics: dict) -> None:
    """タイトル品質ログ読み込み"""
    title_log = session / "title_quality.jsonl"
    if not title_log.exists():
        return

    try:
        issue_counts = {}
        for line in title_log.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            metrics["title"]["total"] += 1
            if entry.get("is_valid", False):
                metrics["title"]["valid"] += 1
            for issue in entry.get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        if metrics["title"]["total"] > 0:
            metrics["title"]["rate"] = metrics["title"]["valid"] / metrics["title"]["total"]
        metrics["title"]["issues"] = sorted(issue_counts.items(), key=lambda x: -x[1])[:5]
    except (json.JSONDecodeError, OSError):
        pass


def _load_tag_metrics(session, metrics: dict) -> None:
    """タグ品質ログ読み込み"""
    tag_log = session / "tag_quality.jsonl"
    if not tag_log.exists():
        return

    try:
        total_consistency = 0.0
        for line in tag_log.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            metrics["tags"]["total"] += 1
            total_consistency += entry.get("consistency_rate", 0.0)
            metrics["tags"]["matched"] += len(entry.get("matched_tags", []))
            metrics["tags"]["unmatched"] += len(entry.get("unmatched_tags", []))
        if metrics["tags"]["total"] > 0:
            metrics["tags"]["avg_consistency"] = total_consistency / metrics["tags"]["total"]
    except (json.JSONDecodeError, OSError):
        pass


def _load_format_metrics(session, metrics: dict) -> None:
    """フォーマット品質ログ読み込み"""
    format_log = session / "format_quality.jsonl"
    if not format_log.exists():
        return

    try:
        issue_counts = {}
        for line in format_log.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            metrics["format"]["total"] += 1
            if entry.get("is_valid", False):
                metrics["format"]["valid"] += 1
            for issue in entry.get("issues", []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        if metrics["format"]["total"] > 0:
            metrics["format"]["rate"] = metrics["format"]["valid"] / metrics["format"]["total"]
        metrics["format"]["common_issues"] = dict(sorted(issue_counts.items(), key=lambda x: -x[1])[:5])
    except (json.JSONDecodeError, OSError):
        pass


def _load_english_metrics(session, metrics: dict) -> None:
    """英語文書判定ログ読み込み"""
    english_log = session / "english_detection.jsonl"
    if not english_log.exists():
        return

    try:
        total_score = 0.0
        for line in english_log.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            entry = json.loads(line)
            metrics["english"]["total"] += 1
            total_score += entry.get("score", 0.0)
            if entry.get("is_complete_english_doc", False):
                metrics["english"]["detected"] += 1
        if metrics["english"]["total"] > 0:
            metrics["english"]["avg_score"] = total_score / metrics["english"]["total"]
    except (json.JSONDecodeError, OSError):
        pass


def _print_metrics(metrics: dict) -> None:
    """メトリクス表示"""
    print(f"\n{'='*60}")
    print("  📊 品質メトリクス")
    print(f"{'='*60}")
    print(f"  セッション: {metrics['session']}")

    # タイトル品質
    print(f"\n📝 タイトル品質:")
    print(f"   処理件数: {metrics['title']['total']}")
    print(f"   有効率: {metrics['title']['rate']*100:.1f}%")
    if metrics["title"]["issues"]:
        print("   頻出問題:")
        for issue, count in metrics["title"]["issues"][:3]:
            print(f"     - {issue}: {count}件")

    # タグ品質
    print(f"\n🏷️ タグ一貫性:")
    print(f"   処理件数: {metrics['tags']['total']}")
    print(f"   平均一貫性率: {metrics['tags']['avg_consistency']*100:.1f}%")
    print(f"   辞書マッチ: {metrics['tags']['matched']}件 / 未マッチ: {metrics['tags']['unmatched']}件")

    # フォーマット品質
    print(f"\n📄 フォーマット準拠:")
    print(f"   処理件数: {metrics['format']['total']}")
    print(f"   準拠率: {metrics['format']['rate']*100:.1f}%")
    if metrics["format"]["common_issues"]:
        print("   頻出問題:")
        for issue, count in list(metrics["format"]["common_issues"].items())[:3]:
            print(f"     - {issue}: {count}件")

    # 英語文書判定
    print(f"\n🌐 英語文書判定:")
    print(f"   処理件数: {metrics['english']['total']}")
    print(f"   英語文書検出: {metrics['english']['detected']}件")
    print(f"   平均スコア: {metrics['english']['avg_score']:.3f}")

    print(f"\n{'='*60}")
