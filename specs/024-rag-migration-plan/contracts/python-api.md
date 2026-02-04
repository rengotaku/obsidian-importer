# Python API Contract

**Feature**: 001-rag-migration-plan
**Date**: 2026-01-18

## Overview

RAG システムの Python API 仕様。内部モジュール間のインターフェース定義。

---

## Module: `src.rag.config`

### Classes

```python
@dataclass
class OllamaConfig:
    """Ollama サーバー設定"""
    local_url: str = "http://localhost:11434"
    remote_url: str = "http://ollama-server.local:11434"
    embedding_model: str = "bge-m3"
    llm_model: str = "gpt-oss:20b"
    embedding_timeout: int = 30
    llm_timeout: int = 120
    num_ctx: int = 65536

@dataclass
class RAGConfig:
    """RAG パイプライン設定"""
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    similarity_threshold: float = 0.5
    embedding_dim: int = 1024
    target_vaults: list[str] = field(default_factory=lambda: [...])
```

---

## Module: `src.rag.clients.ollama`

### Functions

```python
def check_connection(url: str, timeout: int = 5) -> tuple[bool, str | None]:
    """
    Ollama サーバーへの接続確認

    Args:
        url: Ollama サーバー URL
        timeout: タイムアウト秒数

    Returns:
        (success: bool, error_message: str | None)
    """

def get_embedding(
    text: str,
    model: str = "bge-m3",
    url: str = "http://ollama-server.local:11434",
    timeout: int = 30,
) -> tuple[list[float] | None, str | None]:
    """
    テキストの embedding を取得

    Args:
        text: 入力テキスト
        model: embedding モデル名
        url: Ollama サーバー URL
        timeout: タイムアウト秒数

    Returns:
        (embedding: list[float] | None, error: str | None)
    """

def generate_response(
    prompt: str,
    model: str = "gpt-oss:20b",
    url: str = "http://localhost:11434",
    num_ctx: int = 65536,
    timeout: int = 120,
) -> tuple[str | None, str | None]:
    """
    LLM で回答を生成

    Args:
        prompt: プロンプト
        model: LLM モデル名
        url: Ollama サーバー URL
        num_ctx: コンテキストウィンドウサイズ
        timeout: タイムアウト秒数

    Returns:
        (response: str | None, error: str | None)
    """
```

---

## Module: `src.rag.stores.qdrant`

### Functions

```python
def get_document_store(
    path: str | Path = "data/qdrant",
    collection_name: str = "obsidian_knowledge",
    embedding_dim: int = 1024,
    recreate: bool = False,
) -> QdrantDocumentStore:
    """
    Qdrant DocumentStore インスタンスを取得

    Args:
        path: Qdrant データディレクトリ
        collection_name: コレクション名
        embedding_dim: embedding 次元数
        recreate: True の場合、既存コレクションを削除して再作成

    Returns:
        QdrantDocumentStore インスタンス
    """

def get_collection_stats(store: QdrantDocumentStore) -> dict:
    """
    コレクションの統計情報を取得

    Returns:
        {
            "total_chunks": int,
            "total_documents": int,
            "by_vault": {vault_name: {"chunks": int, "documents": int}},
        }
    """
```

---

## Module: `src.rag.pipelines.indexing`

### Functions

```python
def create_indexing_pipeline(
    document_store: QdrantDocumentStore,
    embedding_url: str = "http://ollama-server.local:11434",
    embedding_model: str = "bge-m3",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> Pipeline:
    """
    インデックス作成パイプラインを構築

    Args:
        document_store: Qdrant DocumentStore
        embedding_url: embedding サーバー URL
        embedding_model: embedding モデル名
        chunk_size: チャンクサイズ（トークン数）
        chunk_overlap: オーバーラップサイズ

    Returns:
        Haystack Pipeline
    """

def index_vault(
    pipeline: Pipeline,
    vault_path: Path,
    vault_name: str,
    dry_run: bool = False,
) -> IndexingResult:
    """
    Vault 内のドキュメントをインデックス化

    Args:
        pipeline: インデックスパイプライン
        vault_path: Vault ディレクトリパス
        vault_name: Vault 名
        dry_run: True の場合、処理をシミュレート

    Returns:
        IndexingResult
    """

@dataclass
class IndexingResult:
    """インデックス作成結果"""
    vault: str
    total_files: int
    indexed_files: int
    skipped_files: int
    total_chunks: int
    errors: list[tuple[Path, str]]
    elapsed_seconds: float
```

---

## Module: `src.rag.pipelines.query`

### Functions

```python
def create_search_pipeline(
    document_store: QdrantDocumentStore,
    embedding_url: str = "http://ollama-server.local:11434",
    embedding_model: str = "bge-m3",
    top_k: int = 5,
) -> Pipeline:
    """
    検索パイプラインを構築

    Args:
        document_store: Qdrant DocumentStore
        embedding_url: embedding サーバー URL
        embedding_model: embedding モデル名
        top_k: 取得件数

    Returns:
        Haystack Pipeline
    """

def create_qa_pipeline(
    document_store: QdrantDocumentStore,
    embedding_url: str = "http://ollama-server.local:11434",
    embedding_model: str = "bge-m3",
    llm_url: str = "http://localhost:11434",
    llm_model: str = "gpt-oss:20b",
    top_k: int = 5,
) -> Pipeline:
    """
    Q&A パイプラインを構築

    Args:
        document_store: Qdrant DocumentStore
        embedding_url: embedding サーバー URL
        embedding_model: embedding モデル名
        llm_url: LLM サーバー URL
        llm_model: LLM モデル名
        top_k: 参照ドキュメント数

    Returns:
        Haystack Pipeline
    """

def search(
    pipeline: Pipeline,
    query: str,
    filters: QueryFilters | None = None,
) -> SearchResponse:
    """
    セマンティック検索を実行

    Args:
        pipeline: 検索パイプライン
        query: 検索クエリ
        filters: フィルタ条件

    Returns:
        SearchResponse
    """

def ask(
    pipeline: Pipeline,
    question: str,
    filters: QueryFilters | None = None,
) -> AnswerResponse:
    """
    Q&A を実行

    Args:
        pipeline: Q&A パイプライン
        question: 質問文
        filters: フィルタ条件

    Returns:
        AnswerResponse
    """

@dataclass
class QueryFilters:
    """クエリフィルタ"""
    vaults: list[str] | None = None
    tags: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None

@dataclass
class SearchResult:
    """検索結果項目"""
    score: float
    title: str
    file_path: str
    snippet: str
    vault: str
    tags: list[str]

@dataclass
class SearchResponse:
    """検索レスポンス"""
    query: str
    results: list[SearchResult]
    total: int
    elapsed_ms: int

@dataclass
class AnswerResponse:
    """Q&A レスポンス"""
    question: str
    answer: str
    sources: list[SearchResult]
    confidence: float
    elapsed_ms: int
```

---

## Module: `src.rag.cli`

### Entry Point

```python
def main() -> int:
    """
    CLI エントリポイント

    Returns:
        Exit code (0: success, 1+: error)
    """

# Subcommands
def cmd_index(args: argparse.Namespace) -> int:
    """index サブコマンド"""

def cmd_search(args: argparse.Namespace) -> int:
    """search サブコマンド"""

def cmd_ask(args: argparse.Namespace) -> int:
    """ask サブコマンド"""

def cmd_status(args: argparse.Namespace) -> int:
    """status サブコマンド"""
```

---

## Exception Classes

```python
class RAGError(Exception):
    """RAG システムの基底例外"""
    pass

class ConnectionError(RAGError):
    """サーバー接続エラー"""
    pass

class IndexingError(RAGError):
    """インデックス作成エラー"""
    pass

class QueryError(RAGError):
    """クエリ実行エラー"""
    pass

class ConfigurationError(RAGError):
    """設定エラー"""
    pass
```
