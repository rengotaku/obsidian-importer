"""
@session フォルダ管理モジュール

セッションフォルダの作成と管理を行う。
フォルダ構造: @session/{type}/{session_id}/

Types:
- import: LLMインポート処理
- organize: ファイル整理処理
- test: テスト実行
"""

from pathlib import Path


class FolderManager:
    """
    @sessionフォルダのセッション管理

    Attributes:
        base_path: @sessionのベースパス
    """

    # セッションタイプ別のサブフォルダ定義
    IMPORT_SUBFOLDERS = ["parsed/conversations", "output", "errors"]
    ORGANIZE_SUBFOLDERS: list[str] = []
    TEST_SUBFOLDERS: list[str] = []

    def __init__(self, base_path: Path) -> None:
        """
        Args:
            base_path: @sessionディレクトリのパス
        """
        self.base_path = base_path

    def get_session_dir(self, session_type: str, session_id: str) -> Path:
        """
        セッションフォルダのパスを取得

        Args:
            session_type: セッション種別（import, organize, test）
            session_id: セッションID（YYYYMMDD_HHMMSS形式）

        Returns:
            セッションフォルダのパス
        """
        return self.base_path / session_type / session_id

    def create_session_structure(
        self, session_type: str, session_id: str
    ) -> dict[str, Path]:
        """
        セッションフォルダとサブフォルダを作成

        Args:
            session_type: セッション種別（import, organize, test）
            session_id: セッションID

        Returns:
            作成したフォルダパスの辞書
            - "session": セッションルート
            - "parsed": parsed/conversations/ (import のみ)
            - "output": output/ (import のみ)
            - "errors": errors/ (import のみ)
        """
        session_dir = self.get_session_dir(session_type, session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        paths: dict[str, Path] = {"session": session_dir}

        # タイプ別サブフォルダ作成
        subfolders = self._get_subfolders(session_type)
        for subfolder in subfolders:
            subfolder_path = session_dir / subfolder
            subfolder_path.mkdir(parents=True, exist_ok=True)

            # パス辞書にキーを追加（最後のフォルダ名をキーに）
            key = subfolder.split("/")[0]  # "parsed/conversations" -> "parsed"
            paths[key] = subfolder_path

        return paths

    def _get_subfolders(self, session_type: str) -> list[str]:
        """セッションタイプに応じたサブフォルダリストを返す"""
        if session_type == "import":
            return self.IMPORT_SUBFOLDERS
        elif session_type == "organize":
            return self.ORGANIZE_SUBFOLDERS
        elif session_type == "test":
            return self.TEST_SUBFOLDERS
        return []
