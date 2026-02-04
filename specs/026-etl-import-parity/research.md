# Research: ETL Import パリティ実装

**Generated**: 2026-01-19
**Status**: Complete

## 1. チャンク分割閾値の明確化

**Question**: spec.md で「閾値を超える会話」「適切なサイズ」が曖昧

**Decision**: chunk_size = 25000 文字、overlap_messages = 2

**Rationale**:
- src/converter/scripts/llm_import/common/chunker.py の Chunker クラスがデフォルト値を定義
- 25000 文字は Ollama のコンテキスト長制限に対して安全なマージンを確保
- overlap_messages = 2 により、チャンク間の文脈継続性を維持

**Alternatives considered**:
- トークン数ベース: 実装が複雑化、tiktoken 依存が発生するため却下
- メッセージ数ベース: 短いメッセージが多い会話と長いメッセージが少ない会話で挙動が異なるため却下

**Source**: `src/converter/scripts/llm_import/common/chunker.py:68-76`

---

## 2. @index 重複判定ロジック

**Question**: spec.md で「file_id で重複判定し、異なれば新規作成、同じなら更新」の詳細が不明

**Decision**:
- @index 内の既存ファイルを frontmatter の file_id でスキャン
- 同一 file_id が存在 → 上書き（更新）
- 異なる file_id または file_id なし → 新規作成

**Rationale**:
- file_id はコンテンツ + パスのハッシュであり、内容が変わらなければ同一値
- 再処理時に重複ファイルが増殖するのを防ぐ

**Alternatives considered**:
- ファイル名での重複判定: タイトル変更時に重複が発生するため却下
- 全ファイルスキップ: 更新が反映されないため却下

**Implementation note**:
- UpdateIndexStep で実装
- frontmatter から file_id を抽出するユーティリティは common/knowledge_extractor.py の `extract_file_id_from_frontmatter()` を使用

---

## 3. utils モジュールの配置

**Question**: converter 削除後も機能を維持するための配置戦略

**Decision**: `src/converter/scripts/llm_import/common/` から `src/etl/utils/` にコピー

**Rationale**:
- converter は最終的に削除予定のため、依存を完全に排除
- src/etl 内で完結したパッケージにすることで、将来の移植・配布が容易
- テスト済みコードをそのままコピーすることで信頼性を維持

**コピー対象モジュール**:

| モジュール | コピー先 | 内容 |
|-----------|---------|------|
| ollama.py | src/etl/utils/ollama.py | Ollama API クライアント |
| knowledge_extractor.py | src/etl/utils/knowledge_extractor.py | KnowledgeExtractor, KnowledgeDocument |
| chunker.py | src/etl/utils/chunker.py | Chunker, Chunk, ChunkedConversation |
| file_id.py | src/etl/utils/file_id.py | generate_file_id() |
| error_writer.py | src/etl/utils/error_writer.py | ErrorDetail, write_error_file |

**コピーしないモジュール**:

| モジュール | 理由 |
|-----------|------|
| retry.py | src/etl/core/retry.py（tenacity）で代替 |
| state.py | src/etl/core/models.py（ProcessingItem）で代替 |
| folder_manager.py | src/etl/core/session.py で代替 |
| session_logger.py | フレームワーク自動ログ（BaseStage）で代替 |

**Import 方法**:
```python
# src/etl/stages/transform/knowledge_transformer.py
from src.etl.utils.knowledge_extractor import KnowledgeExtractor, KnowledgeDocument
from src.etl.utils.chunker import Chunker
from src.etl.utils.file_id import generate_file_id
from src.etl.utils.ollama import call_ollama
```

**Alternatives considered**:
- sys.path 操作で converter を参照: 削除予定のため却下
- 共通パッケージとして分離: 別フィーチャーで対応（スコープ外）

---

## 4. DEBUG モード Step 出力の Markdown 構造

**Question**: spec.md で DEBUG モード出力の Markdown フォーマットが未定義

**Decision**: 各 Step の出力は ProcessingItem の状態をそのまま Markdown 化

**Format**:
```markdown
---
item_id: {item_id}
source_path: {source_path}
status: {status}
step: {step_name}
timestamp: {ISO8601}
---

## Content

{content or transformed_content}

## Metadata

{metadata as YAML}
```

**Rationale**:
- Step 間の差分比較が容易
- frontmatter でフィルタリング・検索が可能
- 既存 ProcessingItem の属性をそのまま反映

---

## 5. utils モジュールの統合方法

### KnowledgeExtractor

**コピー元**: `src/converter/scripts/llm_import/common/knowledge_extractor.py`
**コピー先**: `src/etl/utils/knowledge_extractor.py`

**主要メソッド**:
- `extract(conversation)` → ExtractionResult
- `is_english_summary(text)` → bool
- `translate_summary(text)` → str
- `should_chunk(conversation)` → bool
- `extract_chunked(conversation)` → ChunkedResult

**統合先**: ExtractKnowledgeStep.process()

### Chunker

**コピー元**: `src/converter/scripts/llm_import/common/chunker.py`
**コピー先**: `src/etl/utils/chunker.py`

**主要メソッド**:
- `should_chunk(conversation)` → bool
- `split(conversation)` → ChunkedConversation

**統合先**: ExtractKnowledgeStep._handle_large_conversation()

### generate_file_id

**コピー元**: `src/converter/scripts/llm_import/common/file_id.py`
**コピー先**: `src/etl/utils/file_id.py`

**Signature**: `generate_file_id(content: str, filepath: Path) -> str`

**統合先**: GenerateMetadataStep.process()

### ErrorDetail / write_error_file

**コピー元**: `src/converter/scripts/llm_import/common/error_writer.py`
**コピー先**: `src/etl/utils/error_writer.py`

**統合先**: BaseStage._handle_error() または専用 Step

---

## 6. pipeline_stages.jsonl フォーマット

**Question**: フレームワーク自動出力のログフォーマット

**Decision**: 既存 src/converter の session_logger.py と同等フォーマット

**Record structure**:
```json
{
  "timestamp": "2026-01-19T14:30:52.123Z",
  "session_id": "20260119_143052",
  "filename": "conversation_abc123.md",
  "stage": "transform",
  "step": "extract_knowledge",
  "timing_ms": 1234,
  "status": "success",
  "file_id": "abc123def456",
  "skipped_reason": null,
  "before_chars": 5000,
  "after_chars": 1200,
  "diff_ratio": 0.24
}
```

**Implementation**: BaseStage.run() 完了後に自動追記

---

## 7. テスト戦略

**Approach**: 既存 common/ モジュールのテストは維持、src/etl 統合テストを追加

**Test files**:
- `src/etl/tests/test_import_phase.py` - 統合テスト拡張
- `src/etl/tests/test_knowledge_transformer.py` - 新規（Step 単体テスト）

**Mock strategy**:
- Ollama 呼び出しは `unittest.mock.patch` でモック
- ファイル I/O は tempfile で一時ディレクトリを使用

---

## Summary

| 項目 | 決定事項 |
|------|---------|
| チャンク閾値 | 25000 文字、overlap 2 メッセージ |
| @index 重複 | file_id 一致 → 上書き、不一致 → 新規 |
| モジュール配置 | src/converter/common/ → src/etl/utils/ にコピー |
| DEBUG 出力 | ProcessingItem 状態を frontmatter + body 形式 |
| JSONL 形式 | session_logger.py 互換 |
| converter 依存 | 完全排除（コピー後は独立） |
