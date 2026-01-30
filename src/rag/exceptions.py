"""
RAG Exceptions - カスタム例外クラス階層
"""
from __future__ import annotations


class RAGError(Exception):
    """RAG システムの基底例外クラス"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class ConnectionError(RAGError):
    """サーバー接続エラー (Ollama, Qdrant)"""

    def __init__(self, message: str, server: str | None = None, **kwargs):
        details = kwargs.get("details", {})
        if server:
            details["server"] = server
        super().__init__(message, details)
        self.server = server


class IndexingError(RAGError):
    """インデックス操作エラー"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        stage: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if file_path:
            details["file_path"] = file_path
        if stage:
            details["stage"] = stage
        super().__init__(message, details)
        self.file_path = file_path
        self.stage = stage


class QueryError(RAGError):
    """検索・Q&A 操作エラー"""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        stage: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if query:
            details["query"] = query[:100]  # Truncate long queries
        if stage:
            details["stage"] = stage
        super().__init__(message, details)
        self.query = query
        self.stage = stage


class ConfigurationError(RAGError):
    """設定エラー"""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        expected: str | None = None,
        actual: str | None = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        if expected:
            details["expected"] = expected
        if actual:
            details["actual"] = actual
        super().__init__(message, details)
        self.config_key = config_key
        self.expected = expected
        self.actual = actual
