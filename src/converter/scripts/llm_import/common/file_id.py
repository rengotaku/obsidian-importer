"""
file_id - ファイル追跡用ハッシュID生成モジュール

LLMインポート処理で生成されるナレッジファイルを一意に識別するためのIDを生成する。
normalizer の generate_file_id() と同一アルゴリズムを使用（SHA-256先頭12文字）。
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def generate_file_id(content: str, filepath: Path) -> str:
    """ファイルコンテンツと初回パスからハッシュIDを生成

    Args:
        content: ファイルコンテンツ
        filepath: ファイルの相対パス（初回処理時のパス）

    Returns:
        12文字の16進数ハッシュID（SHA-256の先頭48ビット）

    Note:
        - 決定論的: 同一入力に対して常に同一のIDを返す
        - normalizer の generate_file_id() と同一アルゴリズム
        - パスはPOSIX形式に正規化（クロスプラットフォーム対応）
    """
    # コンテンツ + 相対パスを結合してハッシュ化
    # パスは POSIX 形式に正規化（クロスプラットフォーム対応）
    path_str = filepath.as_posix()
    combined = f"{content}\n---\n{path_str}"
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return hash_digest[:12]
