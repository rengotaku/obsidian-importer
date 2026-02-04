# CLI Interface Contract: LLM Import

**Feature**: 015-claude-export-docs
**Date**: 2026-01-16

## 統合CLI: `scripts/llm_import/cli.py`

### Usage

```bash
# プロバイダー指定で実行
python -m scripts.llm_import.cli --provider <provider> <input_dir>

# Claude の場合
python -m scripts.llm_import.cli --provider claude @index/llm_exports/claude/
python -m scripts.llm_import.cli --provider claude @index/llm_exports/claude/ --preview

# ChatGPT の場合（将来）
python -m scripts.llm_import.cli --provider chatgpt @index/llm_exports/chatgpt/
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `input_dir` | path | Yes | エクスポートデータのディレクトリ |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--provider` | `-P` | string | - | **必須**: プロバイダー名（claude, chatgpt） |
| `--output` | `-o` | path | `@index/` | 出力ディレクトリ |
| `--preview` | `-p` | flag | false | プレビューモード（ファイル変更なし） |
| `--no-delete` | | flag | false | 処理後に中間ファイルを削除しない |
| `--status` | `-s` | flag | false | 処理状態を表示して終了 |
| `--reset` | | flag | false | 処理状態をリセット |
| `--single` | | path | none | 単一ファイルのみ処理 |
| `--verbose` | `-v` | flag | false | 詳細ログ出力 |
| `--help` | `-h` | flag | - | ヘルプ表示 |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | 正常終了 |
| 1 | 引数エラー（プロバイダー未指定等） |
| 2 | 入力ディレクトリが存在しない |
| 3 | Ollama API 接続エラー |
| 4 | 処理中に一部エラー発生（部分成功） |
| 5 | 全ファイル処理失敗 |
| 6 | 未対応のプロバイダー |

### Output Format

#### Standard Output (処理サマリー)

```
═══════════════════════════════════════════════════════════
  LLM Import - 処理結果 [claude]
═══════════════════════════════════════════════════════════

処理対象: 150 会話
  ✅ 成功: 142
  ⏭️  スキップ: 5 (短い会話)
  ❌ エラー: 3

出力先: @index/
処理時間: 45分32秒 (平均: 18.2秒/会話)

詳細は状態ファイルを確認: @index/llm_exports/claude/.extraction_state.json
```

#### Preview Mode Output

```
═══════════════════════════════════════════════════════════
  LLM Import - プレビュー [claude]
═══════════════════════════════════════════════════════════

処理対象: 150 会話
  📄 処理予定: 145
  ⏭️  スキップ予定: 5 (短い会話)

サンプル出力 (1/145):
---
ファイル: 2025-12-15_Claude_Code_Setup.md
プロバイダー: claude
タイトル候補: Claude Code セットアップガイド
概要: Claude Code のインストールから初期設定まで...
学び: 3項目
アクション: 2項目
---

実行するには --preview オプションを外してください
```

### State File

処理状態はプロバイダーごとに独立して保存。

**Claude**: `@index/llm_exports/claude/.extraction_state.json`
**ChatGPT**: `@index/llm_exports/chatgpt/.extraction_state.json`

```json
{
  "version": "1.0",
  "provider": "claude",
  "last_run": "2026-01-16T10:30:00+09:00",
  "processed_conversations": {
    "uuid-1234-5678": {
      "id": "uuid-1234-5678",
      "provider": "claude",
      "input_file": "@index/llm_exports/claude/parsed/conversations/2025-12-15_Claude_Code_Setup.md",
      "output_file": "@index/Claude Code セットアップガイド.md",
      "processed_at": "2026-01-16T10:25:30+09:00",
      "status": "success",
      "skip_reason": null,
      "error_message": null
    }
  }
}
```

---

## Entry Points (Claude Code Commands)

### `/og:import-claude`

```bash
# Claude Code CLI で実行
/og:import-claude
/og:import-claude --preview
/og:import-claude @index/llm_exports/claude/claude-data-2026-01-08
```

### `/og:import-chatgpt` (将来)

```bash
/og:import-chatgpt
/og:import-chatgpt --preview
```

### Workflow

1. Phase 1: `providers/<provider>/parser.py` を実行（JSON → Markdown）
2. Phase 2: `common/knowledge_extractor.py` を実行（会話 → ナレッジ）
3. Phase 3: `ollama_normalizer.py --all` を実行（正規化 + Vault 振り分け）

### Common Options

| Option | Description |
|--------|-------------|
| `--preview` | Phase 2 をプレビューモードで実行 |
| `--phase1-only` | Phase 1 のみ実行 |
| `--phase2-only` | Phase 2 のみ実行 |
| `--skip-normalize` | Phase 3 をスキップ |

---

## Provider Interface Contract

新しいプロバイダーを追加する際に実装すべきインターフェース。

### BaseParser (必須)

```python
class BaseParser(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名を返す（例: 'claude', 'chatgpt'）"""
        pass

    @abstractmethod
    def parse(self, export_path: Path) -> list[BaseConversation]:
        """エクスポートデータをパースして会話リストを返す"""
        pass

    @abstractmethod
    def to_markdown(self, conversation: BaseConversation) -> str:
        """会話をMarkdown形式に変換"""
        pass

    def get_output_dir(self) -> Path:
        """Phase 1 出力ディレクトリ"""
        return Path(f"@index/llm_exports/{self.provider_name}/parsed/conversations")
```

### Provider Registration

`scripts/llm_import/providers/__init__.py`:

```python
PROVIDERS = {
    "claude": ClaudeParser,
    "chatgpt": ChatGPTParser,  # 将来
}
```

---

## LLM Prompt Contract

### Input Format (System Prompt → User Message)

**System Prompt**: `scripts/llm_import/prompts/knowledge_extraction.txt` から読み込み

**User Message**:
```
ファイル名: {filename}
プロバイダー: {provider}
会話サマリー: {summary or "なし"}
メッセージ数: {message_count}
会話作成日: {created_at}

--- 会話内容 ---
{conversation_content}
```

### Output Format (JSON)

```json
{
  "title": "会話から抽出した簡潔なタイトル",
  "overview": "会話の目的と主要な成果を1-2段落で説明",
  "key_learnings": [
    "学び1: 具体的な内容",
    "学び2: 具体的な内容",
    "学び3: 具体的な内容"
  ],
  "action_items": [
    "実践可能なアクション1",
    "実践可能なアクション2"
  ],
  "code_snippets": [
    {
      "language": "python",
      "code": "print('Hello')",
      "description": "基本的な出力例"
    }
  ],
  "tags": ["タグ1", "タグ2", "タグ3"],
  "related_keywords": ["キーワード1", "キーワード2"]
}
```

### Validation Rules

| Field | Rule |
|-------|------|
| `title` | 1-200文字、禁止文字なし |
| `overview` | 1-1000文字 |
| `key_learnings` | 1-10項目、各50-500文字 |
| `action_items` | 0-10項目、各10-200文字 |
| `code_snippets` | 0-5項目 |
| `tags` | 1-5個、各1-50文字 |
| `related_keywords` | 1-5個 |
