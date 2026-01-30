# Research: RAG Migration

**Feature**: 001-rag-migration-plan
**Date**: 2026-01-18

## 1. RAG Framework Selection

### Decision: Haystack 2.x

### Rationale
- **パイプライン透明性**: 明示的なパイプライン構造で各ステップが追跡可能
- **構造化ログ**: structlog による JSON 形式のログ出力対応
- **エンタープライズ実績**: 規制業界（金融・医療）での採用実績
- **Ollama 統合**: `ollama-haystack` パッケージで公式サポート

### Alternatives Considered
| Alternative | Rejection Reason |
|-------------|------------------|
| txtai | 可観測性ツールなし、自前実装が必要 |
| LangChain | 過剰な抽象化、デバッグ困難 |
| LlamaIndex | Haystack より監査機能が弱い |

---

## 2. Document Store Selection

### Decision: Qdrant (ローカル永続化モード)

### Rationale
- **ローカル永続化**: ファイルパス指定で自動保存、再起動後も維持
- **フィルタリング**: Vault / tags でのメタデータフィルタリング対応
- **Haystack 統合**: `qdrant-haystack` で公式サポート
- **将来拡張**: Docker 版への移行がスムーズ

### Alternatives Considered
| Alternative | Rejection Reason |
|-------------|------------------|
| InMemoryDocumentStore | 永続化なし、再起動でデータ消失 |
| FAISS | Haystack 2.x で未サポート（開発中） |
| Chroma | フィルタリング機能が Qdrant より弱い |

### Configuration
```python
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

store = QdrantDocumentStore(
    path="./data/qdrant",  # ローカル永続化
    embedding_dim=1024,    # bge-m3
    recreate_index=False,  # 既存インデックス保持
)
```

---

## 3. Embedding Model Selection

### Decision: bge-m3 (BAAI)

### Rationale
- **多言語対応**: 日本語・英語・中国語に最適化（trilingual）
- **最高精度**: ベンチマーク 72%（mxbai 59%, nomic 57%）
- **長文対応**: 8192 トークンのコンテキスト
- **次元数**: 1024（検索精度と効率のバランス）

### Alternatives Considered
| Alternative | Rejection Reason |
|-------------|------------------|
| nomic-embed-text | 日本語最適化なし、精度 57% |
| mxbai-embed-large | 日本語最適化なし、精度 59% |
| multilingual-e5-large | Ollama 未対応 |

### Deployment
- **Host**: `ollama-server.local` (NanoPC-T6, ARM64, 16GB RAM)
- **Ollama Version**: 0.14.2
- **Endpoint**: `http://ollama-server.local:11434/api/embeddings`

---

## 4. LLM Selection

### Decision: gpt-oss:20b (既存モデル継続)

### Rationale
- **既存パイプライン統一**: llm_import / normalizer と同じモデル
- **コンテキストウィンドウ**: 65536 トークン（長文対応）
- **ローカル実行**: プライバシー保護、オフライン動作
- **メモリ効率**: 既にロード済みで追加メモリ不要

### Alternatives Considered
| Alternative | Rejection Reason |
|-------------|------------------|
| qwen2.5:7b | 日本語は優秀だが、既存パイプラインと不統一 |
| Llama-3-ELYZA-JP:8B | コンテキストウィンドウが小さい |

---

## 5. Chunking Strategy

### Decision: 512 トークン / 50 オーバーラップ

### Rationale
- **検索精度**: 小さすぎると文脈喪失、大きすぎると精度低下
- **bge-m3 最適化**: 512 トークンは embedding モデルの推奨サイズ
- **オーバーラップ**: 文の途中切断を防止

### Configuration
```python
from haystack.components.preprocessors import DocumentSplitter

splitter = DocumentSplitter(
    split_by="word",
    split_length=512,
    split_overlap=50,
)
```

---

## 6. Remote Embedding Architecture

### Decision: リモート Ollama サーバー (ollama-server.local)

### Rationale
- **リソース分離**: Embedding 処理をリモートにオフロード
- **メモリ効率**: ローカル PC の負荷軽減
- **並列処理**: LLM とは別サーバーで同時処理可能

### Network Configuration
```
┌─────────────────┐         ┌─────────────────┐
│  Local PC       │         │  NanoPC-T6      │
│  (localhost)    │         │  (ollama-server.local)    │
├─────────────────┤  HTTP   ├─────────────────┤
│ - Qdrant        │◄───────►│ - Ollama        │
│ - gpt-oss:20b   │         │ - bge-m3        │
│ - Haystack      │         │                 │
└─────────────────┘         └─────────────────┘
```

### Fallback Strategy
リモートサーバー不達時はローカル embedding モデル（nomic-embed-text）にフォールバック。

---

## 7. Haystack 2.x Pipeline Patterns

### Indexing Pipeline
```python
from haystack import Pipeline
from haystack.components.converters import MarkdownToDocument
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack_integrations.components.embedders.ollama import OllamaDocumentEmbedder

indexing = Pipeline()
indexing.add_component("converter", MarkdownToDocument())
indexing.add_component("splitter", DocumentSplitter())
indexing.add_component("embedder", OllamaDocumentEmbedder(url="http://ollama-server.local:11434", model="bge-m3"))
indexing.add_component("writer", DocumentWriter(document_store=store))
indexing.connect("converter", "splitter")
indexing.connect("splitter", "embedder")
indexing.connect("embedder", "writer")
```

### Query Pipeline
```python
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.embedders.ollama import OllamaTextEmbedder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

query = Pipeline()
query.add_component("embedder", OllamaTextEmbedder(url="http://ollama-server.local:11434", model="bge-m3"))
query.add_component("retriever", QdrantEmbeddingRetriever(document_store=store, top_k=5))
query.add_component("prompt", PromptBuilder(template=RAG_PROMPT))
query.add_component("llm", OllamaGenerator(url="http://localhost:11434", model="gpt-oss:20b"))
query.connect("embedder.embedding", "retriever.query_embedding")
query.connect("retriever.documents", "prompt.documents")
query.connect("prompt", "llm")
```

---

## 8. Metadata Extraction from Frontmatter

### Decision: YAML frontmatter をドキュメントメタデータとして抽出

### Fields to Extract
| Field | Usage |
|-------|-------|
| `title` | 検索結果表示、ドキュメント識別 |
| `tags` | フィルタリング検索 |
| `created` | 時系列ソート |
| `normalized` | インデックス対象判定（true のみ） |
| `file_path` | ソースファイルへの参照 |
| `vault` | Vault フィルタリング |

### Implementation
```python
import yaml
from pathlib import Path

def extract_metadata(file_path: Path) -> dict:
    content = file_path.read_text()
    if content.startswith("---"):
        _, fm, body = content.split("---", 2)
        meta = yaml.safe_load(fm)
        meta["file_path"] = str(file_path)
        meta["vault"] = file_path.parts[file_path.parts.index("Vaults") + 1]
        return meta, body
    return {}, content
```

---

## Summary

| 項目 | 決定 |
|------|------|
| Framework | Haystack 2.x |
| Document Store | Qdrant (ローカル) |
| Embedding | bge-m3 @ ollama-server.local |
| LLM | gpt-oss:20b @ localhost |
| Chunk Size | 512 tokens / 50 overlap |
| Architecture | 分散（Embedding リモート、LLM ローカル） |
