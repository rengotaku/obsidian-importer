"""
Test utilities for normalizer tests.

環境変数 NORMALIZER_INDEX_DIR を使ってテスト用ディレクトリに切り替える。
"""
from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


@contextmanager
def temp_index_dir() -> Generator[Path, None, None]:
    """
    テスト用の一時 INDEX_DIR を作成するコンテキストマネージャ。

    使用例:
        with temp_index_dir() as index_dir:
            # index_dir は一時ディレクトリのPath
            # NORMALIZER_INDEX_DIR 環境変数が設定されている
            pass
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        old_env = os.environ.get("NORMALIZER_INDEX_DIR")
        os.environ["NORMALIZER_INDEX_DIR"] = str(tmp_path)
        try:
            yield tmp_path
        finally:
            if old_env is None:
                os.environ.pop("NORMALIZER_INDEX_DIR", None)
            else:
                os.environ["NORMALIZER_INDEX_DIR"] = old_env


def get_fixture_path(name: str) -> Path:
    """
    fixtures ディレクトリ内のファイルパスを取得。

    Args:
        name: フィクスチャファイル名（例: "with_frontmatter.md"）

    Returns:
        フィクスチャファイルの絶対パス
    """
    return Path(__file__).parent / "fixtures" / name


def read_fixture(name: str) -> str:
    """
    フィクスチャファイルの内容を読み込む。

    Args:
        name: フィクスチャファイル名

    Returns:
        ファイル内容
    """
    return get_fixture_path(name).read_text(encoding="utf-8")
