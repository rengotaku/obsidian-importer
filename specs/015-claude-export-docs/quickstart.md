# Quickstart: Claude Export Knowledge Extraction

**Feature**: 015-claude-export-docs
**Date**: 2026-01-16

## Prerequisites

- Python 3.11+ (venv: `.venv/`)
- Ollama running locally (`http://localhost:11434`)
- Model: `gpt-oss:20b` (または config.py で設定されたモデル)

## Quick Usage

### 1. データをエクスポート

**Claude の場合:**
1. [claude.ai](https://claude.ai) にアクセス
2. Settings → Export Data
3. ダウンロードした ZIP を展開
4. `@index/llm_exports/claude/` に配置

```
@index/llm_exports/claude/
└── claude-data-2026-01-16-XX-XX-XX-batch-XXXX/
    ├── conversations.json
    ├── memories.json
    └── projects.json
```

**ChatGPT の場合（将来）:**
```
@index/llm_exports/chatgpt/
└── conversations.json
```

### 2. ナレッジ抽出を実行

```bash
# 推奨: /og:import-claude コマンド（Claude Code）
/og:import-claude

# 将来: /og:import-chatgpt

# または統合CLI経由
.venv/bin/python -m scripts.llm_import.cli --provider claude @index/llm_exports/claude/

# 個別実行（Claude）
# Phase 1: JSON → Markdown
.venv/bin/python -m scripts.llm_import.providers.claude.parser @index/llm_exports/claude/claude-data-*

# Phase 2: 会話 → ナレッジ（共通）
.venv/bin/python -m scripts.llm_import.common.knowledge_extractor @index/llm_exports/claude/parsed/conversations

# Phase 3: 正規化 + Vault 振り分け
.venv/bin/python scripts/ollama_normalizer.py --all
```

### 3. 結果を確認

生成されたナレッジドキュメントは各 Vault に配置:
- `エンジニア/` - 技術系の会話
- `ビジネス/` - ビジネス関連
- `経済/` - 経済・金融
- `日常/` - 日常・雑記
- `その他/` - 分類困難なもの

## Development

### プロジェクト構造

```
scripts/
├── llm_import/                     # LLMエクスポートインポーター
│   ├── base.py                     # 共通インターフェース
│   ├── cli.py                      # 統合CLI
│   ├── common/                     # 共通処理
│   │   ├── ollama.py               # Ollama API
│   │   ├── knowledge_extractor.py  # 知識抽出（共通）
│   │   └── state.py                # 状態管理
│   ├── providers/                  # プロバイダー固有
│   │   ├── claude/parser.py        # Claude用パーサー
│   │   └── chatgpt/parser.py       # ChatGPT用（将来）
│   ├── prompts/
│   │   └── knowledge_extraction.txt
│   └── tests/
├── ollama_normalizer.py            # Phase 3 (既存)
└── normalizer/                     # 既存normalizerパッケージ
```

### テスト実行

```bash
# 全テスト
make test

# llm_import パッケージのみ
.venv/bin/python -m pytest scripts/llm_import/tests/ -v
```

### 状態確認

```bash
# 処理状態を表示
.venv/bin/python -m scripts.llm_import.cli --provider claude --status

# 状態リセット
.venv/bin/python -m scripts.llm_import.cli --provider claude --reset
```

### プレビューモード

```bash
# ファイル変更なしで処理結果をプレビュー
.venv/bin/python -m scripts.llm_import.cli --provider claude @index/llm_exports/claude/ --preview
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│           /og:import-claude  |  /og:import-chatgpt          │
│                      (エントリーポイント)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   llm_import/cli.py                         │
│                   (統合CLIエントリー)                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Phase 1     │    │   Phase 2     │    │   Phase 3     │
│ Provider固有  │ →  │ 共通処理      │ →  │ 正規化        │
│ parser.py     │    │ extractor.py  │    │ (既存)        │
└───────────────┘    └───────────────┘    └───────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
   parsed/               @index/             Vault振り分け
   conversations/       *.md (正規化待ち)    エンジニア/etc
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/llm_import/cli.py` | 統合CLIエントリーポイント |
| `scripts/llm_import/base.py` | 共通インターフェース（BaseParser等） |
| `scripts/llm_import/common/knowledge_extractor.py` | 知識抽出（共通） |
| `scripts/llm_import/common/ollama.py` | Ollama API 呼び出し |
| `scripts/llm_import/providers/claude/parser.py` | Claude用パーサー |
| `scripts/llm_import/prompts/knowledge_extraction.txt` | LLM プロンプト |
| `@index/llm_exports/claude/.extraction_state.json` | 処理状態追跡 |

## Troubleshooting

### Ollama 接続エラー

```bash
# Ollama が起動しているか確認
curl http://localhost:11434/api/tags

# 起動していない場合
ollama serve
```

### モデルがない場合

```bash
ollama pull gpt-oss:20b
```

### 処理が遅い場合

- 1会話あたり約15-30秒が目安
- GPU がない場合は時間がかかる
- `--preview` で処理量を事前確認

### エラーが多い場合

```bash
# 状態ファイルでエラー詳細を確認
cat @index/claude/.extraction_state.json | jq '.processed_conversations | to_entries | map(select(.value.status == "error"))'
```
