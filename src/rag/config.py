"""
RAG Configuration - 設定値、定数、パス定義
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# =============================================================================
# Base Paths
# =============================================================================

BASE_DIR = Path(os.environ.get("OBSIDIAN_BASE_DIR", Path(__file__).resolve().parent.parent.parent))
DATA_DIR = BASE_DIR / "data"
QDRANT_PATH = DATA_DIR / "qdrant"
VAULTS_DIR = BASE_DIR / "Vaults"

# =============================================================================
# Ollama Configuration
# =============================================================================


@dataclass
class OllamaConfig:
    """Ollama サーバー設定"""

    # ローカル Ollama (LLM 用)
    local_url: str = "http://localhost:11434"

    # リモート Ollama (Embedding 用 - NanoPC-T6)
    remote_url: str = os.environ.get("OLLAMA_REMOTE_URL", "http://localhost:11434")

    # モデル設定
    embedding_model: str = "bge-m3"
    llm_model: str = "gpt-oss:20b"

    # タイムアウト設定
    embedding_timeout: int = 300  # リモートサーバーのバッチ処理用
    llm_timeout: int = 120

    # バッチサイズ (リモートサーバーの処理能力に合わせて調整)
    embedding_batch_size: int = 5

    # コンテキストウィンドウ
    num_ctx: int = 65536


# =============================================================================
# RAG Pipeline Configuration
# =============================================================================


@dataclass
class RAGConfig:
    """RAG パイプライン設定"""

    # チャンク設定
    chunk_size: int = 512
    chunk_overlap: int = 50

    # 検索設定
    top_k: int = 5
    similarity_threshold: float = 0.5

    # Embedding 次元数 (bge-m3)
    embedding_dim: int = 1024

    # 対象 Vault
    target_vaults: list[str] = field(
        default_factory=lambda: ["エンジニア", "ビジネス", "経済", "日常", "その他"]
    )


# =============================================================================
# Default Instances
# =============================================================================

ollama_config = OllamaConfig()
rag_config = RAGConfig()
