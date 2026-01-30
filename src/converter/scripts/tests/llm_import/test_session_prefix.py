"""
Tests for normalizer/io/session.py prefix functionality
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCreateNewSessionPrefix:
    """create_new_session() のプレフィックス機能テスト"""

    def test_create_new_session_without_prefix(self):
        """プレフィックスなしの場合、従来形式（YYYYMMDD_HHMMSS）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.normalizer.io.session import create_new_session

                session_dir = create_new_session()

                # ディレクトリが作成されている
                assert session_dir.exists()
                assert session_dir.is_dir()
                # 名前が数字とアンダースコアのみ（プレフィックスなし）
                assert session_dir.name[0].isdigit()
                # 直接 plan_dir 下に作成される
                assert session_dir.parent == plan_dir

    def test_create_new_session_with_import_prefix(self):
        """prefix="import" の場合、import/YYYYMMDD_HHMMSS 形式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.normalizer.io.session import create_new_session

                session_dir = create_new_session(prefix="import")

                assert session_dir.exists()
                # セッション名は数字で始まる
                assert session_dir.name[0].isdigit()
                # 親ディレクトリが "import"
                assert session_dir.parent.name == "import"
                assert session_dir.parent.parent == plan_dir

    def test_create_new_session_with_test_prefix(self):
        """prefix="test" の場合、test/YYYYMMDD_HHMMSS 形式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.normalizer.io.session import create_new_session

                session_dir = create_new_session(prefix="test")

                assert session_dir.exists()
                # セッション名は数字で始まる
                assert session_dir.name[0].isdigit()
                # 親ディレクトリが "test"
                assert session_dir.parent.name == "test"

    def test_create_new_session_creates_directory(self):
        """セッションディレクトリが実際に作成される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir = Path(tmpdir)
            with patch("scripts.normalizer.io.session.PLAN_DIR", plan_dir):
                from scripts.normalizer.io.session import create_new_session

                session_dir = create_new_session(prefix="import")

                # import/ サブディレクトリの下に作成
                assert session_dir.parent.name == "import"
                assert session_dir.parent.parent == plan_dir
                assert session_dir.exists()
