# Quickstart: RAG Migration

**Feature**: 001-rag-migration-plan
**Date**: 2026-01-18

## Prerequisites

### 1. Ollama (ローカル)

```bash
# 確認
ollama --version  # 0.14.2 以上推奨

# LLM モデル確認
ollama list | grep gpt-oss
```

### 2. Ollama (リモート: ollama-server.local)

```bash
# 接続確認
ssh -i ~/.ssh/id_ed25519_lan pi@ollama-server.local "ollama --version"

# bge-m3 確認
ssh -i ~/.ssh/id_ed25519_lan pi@ollama-server.local "ollama list | grep bge-m3"

# API 疎通確認
curl -s http://ollama-server.local:11434/api/tags | head
```

### 3. Python 環境

```bash
cd /path/to/project
source development/.venv/bin/activate
python --version  # 3.11+
```

---

## Installation

### 1. 依存パッケージ

```bash
pip install haystack-ai ollama-haystack qdrant-haystack structlog
```

### 2. ディレクトリ作成

```bash
mkdir -p src/rag/{clients,stores,pipelines}
mkdir -p data/qdrant
mkdir -p tests/rag
```

---

## Quick Test

### 1. Embedding 接続テスト

```python
import urllib.request
import json

url = "http://ollama-server.local:11434/api/embeddings"
data = json.dumps({"model": "bge-m3", "prompt": "テスト"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(f"Embedding dim: {len(result['embedding'])}")  # → 1024
```

### 2. Qdrant セットアップテスト

```python
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

store = QdrantDocumentStore(
    path="./data/qdrant",
    embedding_dim=1024,
    recreate_index=True,
)
print(f"Collection created: {store.count_documents()} documents")
```

### 3. 簡易インデックステスト

```python
from haystack import Document

docs = [
    Document(content="Kubernetes はコンテナオーケストレーションツールです。",
             meta={"title": "Kubernetes入門", "vault": "エンジニア"}),
    Document(content="Docker は軽量なコンテナ技術です。",
             meta={"title": "Docker基礎", "vault": "エンジニア"}),
]

# Embedding 取得（リモート）
from haystack_integrations.components.embedders.ollama import OllamaDocumentEmbedder
embedder = OllamaDocumentEmbedder(url="http://ollama-server.local:11434", model="bge-m3")
docs_with_embeddings = embedder.run(documents=docs)["documents"]

# 格納
from haystack.components.writers import DocumentWriter
writer = DocumentWriter(document_store=store)
writer.run(documents=docs_with_embeddings)

print(f"Indexed: {store.count_documents()} documents")
```

### 4. 簡易検索テスト

```python
from haystack_integrations.components.embedders.ollama import OllamaTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

# クエリ embedding
text_embedder = OllamaTextEmbedder(url="http://ollama-server.local:11434", model="bge-m3")
query_embedding = text_embedder.run(text="コンテナ技術について")["embedding"]

# 検索
retriever = QdrantEmbeddingRetriever(document_store=store, top_k=2)
results = retriever.run(query_embedding=query_embedding)

for doc in results["documents"]:
    print(f"[{doc.score:.2f}] {doc.meta['title']}")
```

---

## Usage (After Implementation)

### インデックス作成

```bash
# 全 Vault をインデックス
make rag-index

# 特定 Vault のみ
make rag-index VAULT=エンジニア

# プレビュー（ドライラン）
make rag-index ACTION=preview
```

### 検索

```bash
# 基本検索
make rag-search QUERY="Kubernetes のデプロイ戦略"

# フィルタ付き
make rag-search QUERY="API設計" VAULT=エンジニア

# JSON 出力
make rag-search QUERY="認証" FORMAT=json
```

### Q&A

```bash
# 質問応答
make rag-ask QUERY="OAuth2 と JWT の違いは？"

# 特定 Vault に限定
make rag-ask QUERY="React のパフォーマンス最適化" VAULT=エンジニア
```

### ステータス確認

```bash
make rag-status
```

---

## Troubleshooting

### E001: Ollama server not reachable

```bash
# ローカル Ollama 確認
systemctl status ollama
ollama serve  # 手動起動
```

### E002: Embedding server not reachable

```bash
# リモートサーバー確認
ping ollama-server.local
ssh pi@ollama-server.local "systemctl status ollama"
```

### E003: Qdrant initialization failed

```bash
# パーミッション確認
ls -la data/qdrant/
chmod 755 data/qdrant/

# 再作成
rm -rf data/qdrant/*
make rag-index FORCE=1
```

### E004: No documents found

```bash
# normalized ファイル確認
grep -l "normalized: true" Vaults/エンジニア/**/*.md | head
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User (CLI)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    src/rag/cli.py                           │
│                    (argparse CLI)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│  pipelines/indexing.py  │     │   pipelines/query.py    │
│  - MarkdownToDocument   │     │   - Search Pipeline     │
│  - DocumentSplitter     │     │   - QA Pipeline         │
│  - OllamaDocEmbedder    │     │   - OllamaTextEmbedder  │
│  - DocumentWriter       │     │   - QdrantRetriever     │
└───────────┬─────────────┘     │   - OllamaGenerator     │
            │                   └───────────┬─────────────┘
            │                               │
            ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    stores/qdrant.py                         │
│                  (QdrantDocumentStore)                      │
│                    data/qdrant/                             │
└─────────────────────────────────────────────────────────────┘
            │                               │
            ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   ollama-server.local:11434       │     │   localhost:11434       │
│   (bge-m3 Embedding)    │     │   (gpt-oss:20b LLM)     │
└─────────────────────────┘     └─────────────────────────┘
```
