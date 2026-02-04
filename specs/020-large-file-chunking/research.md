# Research: 大規模ファイルのチャンク分割処理

**Date**: 2026-01-17
**Feature**: 020-large-file-chunking

## Research Tasks

### 1. チャンク分割アルゴリズム

**Decision**: メッセージ境界分割（Message-boundary chunking）

**Rationale**:
- Claude エクスポートは構造化 JSON（`chat_messages` 配列）
- 各メッセージは `role` と `text` を持つ独立オブジェクト
- メッセージ単位で文字数カウント → 閾値到達で分割
- LLM 不要、純粋な文字列処理で実現可能

**Alternatives considered**:
1. **固定長分割**: 実装簡単だがメッセージ途中で切断される → 文脈破壊
2. **セマンティック分割**: LLM で意味単位分割 → 追加 API コスト、処理時間増加
3. **段落分割**: メッセージ内の段落で分割 → 複雑化、効果不明

### 2. オーバーラップ戦略

**Decision**: 末尾 N メッセージをオーバーラップ

**Rationale**:
- 文字数ベースのオーバーラップは実装複雑
- メッセージ単位の方が文脈維持に効果的
- オーバーラップメッセージ数: 2〜3 メッセージ（約 2,000〜3,000 文字相当）

**Implementation**:
```python
# チャンク N の末尾 2 メッセージを チャンク N+1 の先頭に含める
chunk_1: messages[0:50]
chunk_2: messages[48:100]  # overlap: messages[48:50]
```

### 3. 出力戦略

**Decision**: 個別ファイル出力（連番付き）

**Rationale**:
- 各チャンクは独立したナレッジとして価値がある
- 統合処理が不要でシンプル
- 大規模会話は複数トピックを含むため分割出力が自然

**Implementation**:
```python
# ファイル名生成
def get_chunk_filename(title: str, chunk_index: int) -> str:
    return f"{title}_{chunk_index + 1:03d}.md"

# 例: "長い会話" → "長い会話_001.md", "長い会話_002.md", ...
```

### 4. チャンクサイズ閾値

**Decision**: 25,000 文字（安全マージン含む）

**Rationale**:
- num_ctx: 65,536 トークン（更新済み）
- 日本語: 1文字 ≈ 1.5〜2 トークン
- 25,000 文字 ≈ 37,500〜50,000 トークン
- システムプロンプト + 出力用に余裕を確保

**Note**: spec の 30,000 文字は num_ctx=16,384 時代の値。拡張済みなので安全マージンとして 25,000 を採用。

### 5. エラーハンドリング

**Decision**: チャンク単位のリトライ

**Rationale**:
- 1 チャンク失敗 → そのチャンクのみリトライ
- 成功チャンクは保持
- 全チャンク失敗 → 会話全体をエラーとして記録

**Implementation**:
```python
results = []
for i, chunk in enumerate(chunks):
    result = process_chunk(chunk)
    if not result.success:
        result = retry_chunk(chunk, max_retries=2)
    results.append(result)
```

## Technical Decisions Summary

| Item | Decision | Spec Reference |
|------|----------|----------------|
| 分割単位 | メッセージ境界 | FR-002 |
| オーバーラップ | 末尾 2 メッセージ | FR-003 |
| チャンクサイズ | 25,000 文字 | FR-001（調整） |
| 出力形式 | 連番付き個別ファイル | FR-004 |
| 進捗ログ | チャンク N/M 形式 | FR-005 |

## Dependencies

- 既存: `KnowledgeExtractor` クラス
- 既存: `call_ollama()` 関数
- 新規: `Chunker` クラス（新規モジュール）

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| 単一メッセージがチャンクサイズ超過 | そのメッセージを 1 チャンクとして処理（警告ログ出力） |
| 重複学びの蓄積 | 正規化後に重複除去 |
| オーバーラップによる処理時間増加 | 2 メッセージのみで最小限に抑制 |
