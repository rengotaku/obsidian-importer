# CLI Interface Contract

**Feature**: 001-rag-migration-plan
**Date**: 2026-01-18

## Overview

RAG システムの CLI インターフェース仕様。Makefile 経由での実行を想定。

---

## Commands

### `rag index`

Vault 内のドキュメントをインデックス化する。

```bash
# Usage
python -m src.rag.cli index [OPTIONS]

# Options
--vault VAULT       対象 Vault (複数指定可、省略時は全 Vault)
--force             既存インデックスを削除して再作成
--dry-run           実際の処理を行わずプレビュー
--verbose           詳細ログ出力
```

**Examples**:
```bash
# 全 Vault をインデックス
make rag-index

# 特定 Vault のみ
make rag-index VAULT=エンジニア

# プレビューモード
make rag-index ACTION=preview
```

**Exit Codes**:
| Code | Description |
|------|-------------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 引数エラー |
| 3 | 接続エラー (Ollama/Qdrant) |

---

### `rag search`

セマンティック検索を実行する。

```bash
# Usage
python -m src.rag.cli search QUERY [OPTIONS]

# Arguments
QUERY               検索クエリ（必須）

# Options
--vault VAULT       対象 Vault (複数指定可)
--tag TAG           タグフィルタ (複数指定可、AND 条件)
--top-k N           取得件数 (デフォルト: 5)
--threshold FLOAT   類似度閾値 (デフォルト: 0.5)
--format FORMAT     出力形式 (json/text、デフォルト: text)
```

**Examples**:
```bash
# 基本検索
make rag-search QUERY="Kubernetes のデプロイ戦略"

# フィルタ付き検索
make rag-search QUERY="API設計" VAULT=エンジニア TAG=REST

# JSON 出力
make rag-search QUERY="認証" FORMAT=json
```

**Output (text)**:
```
Found 5 results for "Kubernetes のデプロイ戦略"

1. [0.92] Kubernetes Blue-Green デプロイメント
   Vaults/エンジニア/kubernetes/blue-green.md
   ...Blue-Green デプロイは、2つの同一環境を用意し...

2. [0.87] Kubernetes Canary リリース戦略
   Vaults/エンジニア/kubernetes/canary.md
   ...Canary リリースでは、新バージョンを一部のユーザーに...
```

**Output (json)**:
```json
{
  "query": "Kubernetes のデプロイ戦略",
  "results": [
    {
      "score": 0.92,
      "title": "Kubernetes Blue-Green デプロイメント",
      "file_path": "Vaults/エンジニア/kubernetes/blue-green.md",
      "snippet": "...Blue-Green デプロイは、2つの同一環境を用意し...",
      "vault": "エンジニア",
      "tags": ["kubernetes", "deployment"]
    }
  ],
  "total": 5,
  "elapsed_ms": 1250
}
```

---

### `rag ask`

Q&A モードで質問に回答する。

```bash
# Usage
python -m src.rag.cli ask QUESTION [OPTIONS]

# Arguments
QUESTION            質問文（必須）

# Options
--vault VAULT       対象 Vault (複数指定可)
--tag TAG           タグフィルタ (複数指定可)
--top-k N           参照ドキュメント数 (デフォルト: 5)
--format FORMAT     出力形式 (json/text、デフォルト: text)
--no-sources        出典を非表示
```

**Examples**:
```bash
# 基本質問
make rag-ask QUERY="OAuth2 と JWT の違いは？"

# 特定 Vault に限定
make rag-ask QUERY="React のパフォーマンス最適化方法" VAULT=エンジニア
```

**Output (text)**:
```
Q: OAuth2 と JWT の違いは？

A: OAuth2 は認可のためのフレームワークであり、JWTはトークンの形式です。
OAuth2 はアクセストークンを発行する仕組みを定義し、JWT はそのトークンの
具体的なフォーマット（署名付き JSON）を規定しています。つまり、OAuth2 の
アクセストークンとして JWT を使用することが一般的です。

Sources:
- [1] OAuth2 認可フロー (Vaults/エンジニア/auth/oauth2.md)
- [2] JWT トークン構造 (Vaults/エンジニア/auth/jwt.md)
- [3] 認証と認可の違い (Vaults/エンジニア/auth/authn-authz.md)
```

**Output (json)**:
```json
{
  "question": "OAuth2 と JWT の違いは？",
  "answer": "OAuth2 は認可のためのフレームワークであり...",
  "sources": [
    {
      "title": "OAuth2 認可フロー",
      "file_path": "Vaults/エンジニア/auth/oauth2.md",
      "score": 0.91,
      "snippet": "..."
    }
  ],
  "confidence": 0.88,
  "elapsed_ms": 3200
}
```

---

### `rag status`

インデックスの状態を表示する。

```bash
# Usage
python -m src.rag.cli status [OPTIONS]

# Options
--vault VAULT       特定 Vault の状態のみ表示
--format FORMAT     出力形式 (json/text)
```

**Output (text)**:
```
RAG Index Status
================

Collection: obsidian_knowledge
Total Chunks: 4,532
Total Documents: 892

By Vault:
  エンジニア:  2,105 chunks (423 docs)
  ビジネス:     891 chunks (189 docs)
  経済:         756 chunks (145 docs)
  日常:         512 chunks (98 docs)
  その他:       268 chunks (37 docs)

Last Updated: 2026-01-18 14:30:00
Embedding Model: bge-m3 @ ollama-server.local
```

---

## Makefile Targets

```makefile
# RAG targets
.PHONY: rag-index rag-search rag-ask rag-status

rag-index:
	$(PYTHON) -m src.rag.cli index $(if $(VAULT),--vault $(VAULT)) \
		$(if $(filter preview,$(ACTION)),--dry-run) \
		$(if $(FORCE),--force)

rag-search:
	$(PYTHON) -m src.rag.cli search "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT)) \
		$(if $(TAG),--tag $(TAG)) \
		$(if $(TOP_K),--top-k $(TOP_K)) \
		$(if $(FORMAT),--format $(FORMAT))

rag-ask:
	$(PYTHON) -m src.rag.cli ask "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT)) \
		$(if $(TAG),--tag $(TAG)) \
		$(if $(FORMAT),--format $(FORMAT))

rag-status:
	$(PYTHON) -m src.rag.cli status \
		$(if $(VAULT),--vault $(VAULT)) \
		$(if $(FORMAT),--format $(FORMAT))
```

---

## Error Messages

| Code | Message | Action |
|------|---------|--------|
| `E001` | Ollama server not reachable | Check Ollama is running |
| `E002` | Embedding server not reachable | Check ollama-server.local is accessible |
| `E003` | Qdrant initialization failed | Check data/qdrant permissions |
| `E004` | No documents found | Check Vault paths and normalized flag |
| `E005` | Query too long | Limit query to 1000 characters |
| `E006` | Invalid vault name | Use: エンジニア, ビジネス, 経済, 日常, その他 |
