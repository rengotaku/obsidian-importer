# Research: too_large 判定の LLM コンテキストベース化

**Feature**: 038-too-large-llm-context
**Created**: 2026-01-27

## 調査項目

### 1. 現状の too_large 判定ロジック

**調査結果**:

`ExtractKnowledgeStep.process()` (knowledge_transformer.py:151-266) で以下のように判定：

```python
if not chunk_enabled and not is_chunked and item.content:
    content_size = len(item.content)  # ← 生 JSON 全体
    if content_size > self._chunk_size:  # 25000 chars
        # Skip LLM processing, mark as too_large
        item.status = ItemStatus.SKIPPED
        item.metadata["skipped_reason"] = "too_large"
        ...
```

**問題点**:
- `item.content` は生 JSON 全体（メタデータ、重複テキスト含む）
- 実際の LLM コンテキスト: メッセージ `text` のみ
- 実測オーバーヘッド: **61.7%**（28,371 chars → 10,863 chars）

### 2. LLM コンテキスト構築の詳細

**調査結果**:

`KnowledgeExtractor._build_user_message()` (knowledge_extractor.py:469-510):

```python
def _build_user_message(self, conversation, exclude_summary=False) -> str:
    lines = []
    # ヘッダー（~200 chars）
    lines.append(f"ファイル名: {conversation.title}")
    lines.append(f"プロバイダー: {conversation.provider}")
    lines.append(f"会話サマリー: {summary or 'なし'}")
    lines.append(f"メッセージ数: {len(conversation.messages)}")
    lines.append(f"会話作成日: {conversation.created_at}")
    lines.append("--- 会話内容 ---")

    # メッセージ（メイン）
    for msg in conversation.messages:
        role_label = "User" if msg.role == "user" else "Assistant"
        lines.append(f"[{role_label}]")  # ~15 chars/msg
        lines.append(msg.content.strip())  # ← 実際に必要なデータ

    return "\n".join(lines)
```

**LLM コンテキストサイズの計算式**:
```
LLM_context_size = ヘッダー(~200) + Σ(message.text) + Σ(ラベル ~15/msg)
```

### 3. Claude エクスポート JSON 構造

**調査結果**:

```json
{
  "uuid": "...",
  "name": "会話タイトル",
  "summary": "...",
  "created_at": "...",
  "updated_at": "...",
  "account": {"uuid": "..."},
  "chat_messages": [
    {
      "uuid": "...",
      "text": "メッセージ本文",           // ← LLM に渡す
      "content": [
        {
          "text": "メッセージ本文",       // ← 重複！
          "type": "text",
          "start_timestamp": "...",
          "stop_timestamp": "...",
          "flags": null,
          "citations": []
        }
      ],
      "sender": "human",
      "created_at": "...",
      "updated_at": "...",
      "attachments": [],
      "files": []
    }
  ]
}
```

**オーバーヘッドの内訳**:
- `text` と `content[0].text` の重複: ~100%
- メッセージメタデータ（uuid, timestamps等）: ~200 chars/msg
- 会話メタデータ（uuid, account等）: ~200 chars
- JSON 構造（括弧、キー名）: ~20%

### 4. 判定タイミングの検討

**現状**:
- 判定: `ExtractKnowledgeStep.process()` 内
- データ: `item.content`（生 JSON 文字列）
- conversation オブジェクト: 判定後に構築

**修正オプション**:

| オプション | 利点 | 欠点 |
|-----------|------|------|
| A. JSON パース前に概算計算 | パース不要 | 精度低い |
| B. JSON パース後、conversation 構築前に計算 | 精度高い | パースコスト |
| C. conversation 構築後に計算 | 最高精度 | 構築コスト |

**Decision**: オプション B を採用
- JSON パースは必須処理（後続で必要）
- `chat_messages` から `text` を抽出して計算
- conversation 構築前に判定できる

### 5. ChatGPT エクスポートとの互換性

**調査結果**:

ChatGPT エクスポートの構造（`mapping` ベース）：
```python
# openai_extractor.py での処理
for msg in conversation.messages:
    content = msg.get("text", "")  # または content フィールド
```

**互換性**: 両方とも `text` フィールドを使用しており、計算ロジックは共通化可能

## 設計決定

### Decision 1: LLM コンテキストサイズ計算関数

```python
def calculate_llm_context_size(data: dict) -> int:
    """LLM に渡す実際のコンテキストサイズを計算する。

    Args:
        data: パース済み会話 JSON

    Returns:
        推定 LLM コンテキストサイズ（文字数）
    """
    HEADER_SIZE = 200  # 固定ヘッダー部分
    LABEL_OVERHEAD = 15  # "[User]\n" or "[Assistant]\n" + 改行

    messages = data.get("chat_messages", [])

    # メッセージ text の合計
    message_size = sum(len(msg.get("text", "")) for msg in messages)

    # ラベルオーバーヘッド
    label_size = len(messages) * LABEL_OVERHEAD

    return HEADER_SIZE + message_size + label_size
```

**Rationale**:
- シンプルで高速
- 実際の `_build_user_message()` 出力との差は 10% 以内
- JSON パース後、conversation 構築前に実行可能

### Decision 2: 判定ロジックの修正箇所

**修正対象**: `ExtractKnowledgeStep.process()` (knowledge_transformer.py)

**変更前**:
```python
if not chunk_enabled and not is_chunked and item.content:
    content_size = len(item.content)
    if content_size > self._chunk_size:
```

**変更後**:
```python
if not chunk_enabled and not is_chunked and item.content:
    data = json.loads(item.content)  # JSON パースを先に実行
    llm_context_size = self._calculate_llm_context_size(data)
    if llm_context_size > self._chunk_size:
```

**Rationale**:
- JSON パースは後続処理で必要なため、先に実行しても無駄がない
- too_large でスキップする場合も、パース済みデータは破棄
- 正常処理の場合、パースを再実行しないよう `data` を再利用

### Decision 3: テスト戦略

1. **ユニットテスト**: `calculate_llm_context_size()` の単体テスト
2. **統合テスト**: 新旧判定結果の比較
3. **回帰テスト**: 既存テストケースとの互換性確認

## Alternatives Considered

### Alternative A: _build_user_message() を直接呼び出す

**却下理由**:
- conversation オブジェクト構築が必要（コスト高）
- too_large でスキップする場合に無駄な処理

### Alternative B: ヒューリスティック係数で概算

```python
estimated_size = len(item.content) * 0.4  # 約 40% が実データ
```

**却下理由**:
- 精度が低い（会話によってオーバーヘッド率が異なる）
- 仕様の SC-001（10% 以内）を満たせない可能性

## 残課題

なし - すべての NEEDS CLARIFICATION が解決済み
