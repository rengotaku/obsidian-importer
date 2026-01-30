#!/usr/bin/env python3
"""
Ollama Genre Classifier for Obsidian files
要確認・未確認ファイルをOllamaで自動ジャンル判定し、CSVを更新
標準ライブラリのみ使用
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# 設定
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")
BASE_DIR = Path(os.environ.get("OBSIDIAN_BASE_DIR", Path(__file__).resolve().parent.parent.parent))
CSV_PATH = BASE_DIR / "@index/全ファイル一覧.csv"
RESULT_PATH = BASE_DIR / "@index/ジャンル判定結果.csv"

# ジャンル判定用システムプロンプト
SYSTEM_PROMPT = """あなたはファイル分類AIです。ファイルの内容を読み、以下の4つのジャンルから最適なものを1つ選んでください:
- エンジニア: 技術、プログラミング、システム設計、インフラ、DevOps、AI/ML技術
- ビジネス: ビジネス書、マネジメント、キャリア、コミュニケーション
- 経済: 経済ニュース、投資、市場分析、金融
- 日常: 日常生活、趣味、雑記、その他

回答はJSON形式のみで: {"genre": "ジャンル名", "confidence": 0.0-1.0, "reason": "理由（30字以内）"}"""


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """プログレスバーを生成"""
    percent = current / total
    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{total} ({percent*100:.1f}%)"


def find_file(filename: str) -> Path | None:
    """ファイル名からファイルパスを検索"""
    for vault in ["エンジニア", "ビジネス", "経済", "日常"]:
        # 直接検索
        direct = BASE_DIR / vault / f"{filename}.md"
        if direct.exists():
            return direct
        # 再帰検索
        for p in (BASE_DIR / vault).rglob(f"{filename}.md"):
            return p
    return None


def read_file_content(filepath: Path, max_chars: int = 2000) -> str:
    """ファイル内容を読み込み（先頭部分のみ）"""
    try:
        content = filepath.read_text(encoding="utf-8")
        # frontmatter以降の内容を抽出
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]
        return content[:max_chars].strip()
    except Exception as e:
        return f"読み込みエラー: {e}"


def classify_with_ollama(filename: str, content: str) -> dict:
    """Ollamaでジャンル判定（標準ライブラリ使用）"""
    user_message = f"ファイル名: {filename}\n\n内容:\n{content}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            answer = result.get("message", {}).get("content", "{}")
            # JSON部分を抽出
            if "{" in answer and "}" in answer:
                json_str = answer[answer.find("{"):answer.rfind("}")+1]
                return json.loads(json_str)
            return {"genre": "不明", "confidence": 0, "reason": "JSON解析失敗"}
    except urllib.error.URLError as e:
        return {"genre": "エラー", "confidence": 0, "reason": f"接続エラー: {str(e)[:20]}"}
    except TimeoutError:
        return {"genre": "エラー", "confidence": 0, "reason": "タイムアウト"}
    except Exception as e:
        return {"genre": "エラー", "confidence": 0, "reason": str(e)[:30]}


def main():
    print("=" * 60)
    print("Ollama ジャンル判定ツール")
    print("=" * 60)

    # CSVを読み込み（BOM付きUTF-8対応）
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        fieldnames = reader.fieldnames

    # 要確認・未確認のファイルを抽出
    target_indices = []
    for i, row in enumerate(all_rows):
        status = row.get("ジャンル適合", "")
        if "確認" in status:
            target_indices.append(i)

    total = len(target_indices)
    print(f"対象ファイル数: {total}")
    print("-" * 60)

    results = []
    stats = {"OK": 0, "要移動": 0, "エラー": 0}

    for count, idx in enumerate(target_indices, 1):
        row = all_rows[idx]
        filename = row["ファイル名"]
        current_vault = row["vault"]
        current_status = row["ジャンル適合"]

        # 進捗表示
        sys.stdout.write(f"\r{progress_bar(count, total)} ")
        sys.stdout.flush()

        # ファイルを検索
        filepath = find_file(filename)
        if not filepath:
            results.append({
                "ファイル名": filename,
                "現在vault": current_vault,
                "現在ステータス": current_status,
                "判定ジャンル": "不明",
                "確信度": 0,
                "理由": "ファイル未発見",
                "移動要否": "-"
            })
            stats["エラー"] += 1
            continue

        # 内容を読み込み
        content = read_file_content(filepath)
        if content.startswith("読み込みエラー"):
            results.append({
                "ファイル名": filename,
                "現在vault": current_vault,
                "現在ステータス": current_status,
                "判定ジャンル": "エラー",
                "確信度": 0,
                "理由": content[:30],
                "移動要否": "-"
            })
            stats["エラー"] += 1
            continue

        # Ollamaで判定
        result = classify_with_ollama(filename, content)
        genre = result.get("genre", "不明")
        confidence = result.get("confidence", 0)
        reason = result.get("reason", "")[:50]

        # 移動要否を判定（確信度0.7以上のみ移動対象）
        valid_genres = ["エンジニア", "ビジネス", "経済", "日常"]
        confidence_threshold = 0.7

        if genre in valid_genres and confidence >= confidence_threshold:
            if genre != current_vault:
                need_move = "要移動"
                stats["要移動"] += 1
                # 元CSVを更新: ジャンル適合を判定結果に
                all_rows[idx]["ジャンル適合"] = f"→{genre}"
            else:
                need_move = "OK"
                stats["OK"] += 1
                # 元CSVを更新: OKに
                all_rows[idx]["ジャンル適合"] = "OK"
        elif genre in valid_genres:
            # 確信度が低い場合は要確認
            need_move = "要確認"
            stats["要確認"] = stats.get("要確認", 0) + 1
            all_rows[idx]["ジャンル適合"] = f"要確認({genre}?)"
        else:
            need_move = "-"
            stats["エラー"] += 1

        results.append({
            "ファイル名": filename,
            "現在vault": current_vault,
            "現在ステータス": current_status,
            "判定ジャンル": genre,
            "確信度": confidence,
            "理由": reason,
            "移動要否": need_move
        })

        # API負荷軽減
        time.sleep(0.3)

    print()  # 改行
    print("-" * 60)

    # 判定結果CSVを出力
    with open(RESULT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ファイル名", "現在vault", "現在ステータス",
            "判定ジャンル", "確信度", "理由", "移動要否"
        ])
        writer.writeheader()
        writer.writerows(results)
    print(f"判定結果: {RESULT_PATH}")

    # 元CSVを更新
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"CSV更新完了: {CSV_PATH}")

    # 統計表示
    print("-" * 60)
    print("📊 統計:")
    print(f"  ✅ OK（現vault維持）: {stats['OK']}")
    print(f"  📁 要移動: {stats['要移動']}")
    print(f"  ⚠️ 要確認（確信度<0.7）: {stats.get('要確認', 0)}")
    print(f"  ❌ エラー: {stats['エラー']}")
    print("=" * 60)

    # 要移動ファイルの詳細を表示
    if stats["要移動"] > 0:
        print("\n📁 移動が必要なファイル:")
        for r in results:
            if r["移動要否"] == "要移動":
                print(f"  {r['ファイル名']}: {r['現在vault']} → {r['判定ジャンル']}")


if __name__ == "__main__":
    main()
