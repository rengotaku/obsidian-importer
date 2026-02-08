# Phase 2 Output

## 作業概要
- Phase 2 - US1 Claude Extract パイプライン (GREEN) の実装完了
- FAIL テスト 17 件をすべて PASS させた
- Claude エクスポート JSON から ParsedItem への変換ロジックを実装

## 修正ファイル一覧

### 実装ファイル
- `src/obsidian_etl/pipelines/extract_claude/nodes.py` - parse_claude_json ノード実装
  - Claude JSON パース
  - 構造バリデーション (uuid, chat_messages 必須)
  - コンテンツバリデーション (空メッセージ除外、最小メッセージ数3)
  - チャンク分割 (25000文字超)
  - file_id 生成 (SHA256 ハッシュ)
  - フォールバック会話名生成 (name が None/欠落時)

- `src/obsidian_etl/pipelines/extract_claude/pipeline.py` - パイプライン定義
  - raw_claude_conversations → parsed_items の変換パイプライン

### テスト結果
```
Ran 17 tests in 0.001s

OK
```

全テストが PASS:
- `test_parse_claude_json_basic`: 基本パース動作
- `test_parse_claude_json_message_format`: メッセージ正規化
- `test_parse_claude_json_content_format`: コンテンツフォーマット
- `test_parse_claude_json_second_conversation`: 複数会話処理
- `test_parse_claude_json_chunking`: 25000文字超のチャンク分割
- `test_parse_claude_json_skip_short`: メッセージ3件未満の除外
- `test_parse_claude_json_empty_conversations`: 空配列ハンドリング
- `test_parse_claude_json_missing_name`: name=None フォールバック
- `test_parse_claude_json_name_missing_key`: name キー欠落フォールバック
- `test_validate_structure_missing_uuid`: uuid 欠落の除外
- `test_validate_structure_missing_chat_messages`: chat_messages 欠落の除外
- `test_validate_structure_both_required_present`: 正常構造の処理
- `test_validate_content_empty_messages`: 全空メッセージの除外
- `test_validate_content_mixed_empty_messages`: 部分空メッセージのフィルタリング
- `test_file_id_generation`: SHA256 file_id 生成
- `test_file_id_deterministic`: file_id の決定性
- `test_file_id_different_for_different_content`: 異なるコンテンツで異なる file_id

## 実装の詳細

### parse_claude_json ノード

**入力**: `list[dict]` (Claude conversations.json)

**出力**: `dict[str, dict]` (partition_id → ParsedItem dict)

**処理フロー**:
1. 構造バリデーション (uuid, chat_messages 必須)
2. 空メッセージのフィルタリング
3. 最小メッセージ数チェック (MIN_MESSAGES = 3)
4. メッセージ正規化 (sender → role, text → content)
5. コンテンツフォーマット ("Human:" / "Assistant:" プレフィックス)
6. コンテンツ長バリデーション (MIN_CONTENT_LENGTH = 10)
7. 会話名フォールバック (name が None/欠落 → 最初の human メッセージ)
8. file_id 生成 (SHA256 ハッシュ先頭12文字)
9. チャンク分割 (should_chunk / split_messages 使用)
10. ParsedItem dict 生成

### ParsedItem 構造 (data-model.md E-2 準拠)

```python
{
    "item_id": str,               # conversation uuid or chunk file_id
    "source_provider": "claude",
    "source_path": str,           # virtual path (conversations/{uuid}.md)
    "conversation_name": str | None,
    "created_at": str | None,     # ISO 8601
    "messages": list[dict],       # [{role, content}]
    "content": str,               # formatted conversation text
    "file_id": str,               # SHA256 12-char hash
    "is_chunked": bool,
    "chunk_index": int | None,
    "total_chunks": int | None,
    "parent_item_id": str | None,
}
```

### チャンク分割ロジック

- `obsidian_etl.utils.chunker.should_chunk()` で 25000文字超を検出
- `obsidian_etl.utils.chunker.split_messages()` でメッセージ境界で分割
- チャンクメタデータ (is_chunked, chunk_index, total_chunks, parent_item_id) を各チャンクに付与
- partition_id: `{parent_file_id}_chunk{index}` 形式

### file_id 生成

- `obsidian_etl.utils.file_id.generate_file_id(content, source_path)` を使用
- SHA256 ハッシュの先頭12文字 (48ビット)
- content + source_path を組み合わせて一意性を保証

## 注意点

### 次 Phase で必要な情報
- ParsedItem 構造は data-model.md E-2 に準拠
- Transform パイプライン (Phase 3) の入力として使用可能
- PartitionedDataset として永続化する際は `data/02_intermediate/parsed/` に配置

### 既存コードとの差異
- 旧実装 (src/etl/stages/extract/claude_extractor.py) は ProcessingItem dataclass を使用
- 新実装は dict ベースで Kedro PartitionedDataset に適合
- チャンク分割のタイミングは同じ (Extract 段階)
- file_id 生成ロジックは既存 utils を再利用

## 実装のミス・課題

なし。全テストが PASS し、RED テスト要件をすべて満たしている。

## 次のステップ

Phase 3 (US1 Transform パイプライン) への移行:
- ParsedItem → TransformedItem 変換
- LLM 知識抽出 (extract_knowledge ノード)
- メタデータ生成 (generate_metadata ノード)
- Markdown フォーマット (format_markdown ノード)
