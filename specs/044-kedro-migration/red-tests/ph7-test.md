# Phase 7 RED Tests

## サマリー
- Phase: Phase 7 - US3 OpenAI (ChatGPT) プロバイダー
- FAIL テスト数: 35 (7 テストクラス)
- テストファイル: tests/pipelines/extract_openai/test_nodes.py

## FAIL テスト一覧

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|---------|
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_returns_dict | parse_chatgpt_zip が dict を返す |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_item_count | 2 会話から 2 ParsedItem 生成 |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_parsed_item_structure | E-2 スキーマ準拠 (item_id, source_provider, messages, file_id 等) |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_conversation_name | タイトルから conversation_name 設定 |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_message_format | {role, content} 形式に正規化 |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_content_format | Human:/Assistant: フォーマット済みテキスト |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_file_id_is_valid_hex | 12 桁 16 進数 file_id |
| TestParseChatgptZipBasic | test_parse_chatgpt_zip_golden_data_match | ゴールデンデータとの部分一致 |
| TestChatgptTreeTraversal | test_linear_tree_traversal | 線形ツリー → 時系列順メッセージ |
| TestChatgptTreeTraversal | test_branching_tree_follows_current_node | 分岐ツリーで current_node パスのみ使用 |
| TestChatgptTreeTraversal | test_system_node_in_tree_excluded | system ノード除外 |
| TestChatgptMultimodal | test_image_placeholder | 画像 → [Image: asset_pointer] |
| TestChatgptMultimodal | test_audio_placeholder | 音声 → [Audio: filename] |
| TestChatgptMultimodal | test_mixed_multimodal_parts | テキスト+画像+音声の混在処理 |
| TestChatgptRoleConversion | test_user_becomes_human | user → human 変換 |
| TestChatgptRoleConversion | test_assistant_remains_assistant | assistant 維持 |
| TestChatgptRoleConversion | test_system_excluded | system 除外 |
| TestChatgptRoleConversion | test_tool_excluded | tool 除外 |
| TestChatgptRoleConversion | test_only_valid_roles_in_output | human/assistant のみ出力 |
| TestChatgptChunking | test_large_conversation_chunked | 25000+ chars → 複数チャンク |
| TestChatgptChunking | test_chunk_metadata_fields | is_chunked, chunk_index, total_chunks, parent_item_id |
| TestChatgptChunking | test_chunk_indices_sequential | 0-based 連番 |
| TestChatgptChunking | test_chunks_share_parent_item_id | 同一 parent_item_id 共有 |
| TestChatgptChunking | test_chunks_have_openai_provider | source_provider="openai" |
| TestChatgptChunking | test_short_conversation_not_chunked | 25000 未満はチャンクなし |
| TestChatgptEmptyConversations | test_empty_conversations_json | 空 JSON → 空 dict |
| TestChatgptEmptyConversations | test_no_zip_files_in_input | 空入力 → 空 dict |
| TestChatgptEmptyConversations | test_short_conversation_skipped | < 3 messages → スキップ |
| TestChatgptEmptyConversations | test_missing_title_fallback | title=None → 最初のユーザーメッセージ |
| TestChatgptEmptyConversations | test_missing_timestamp_fallback | create_time=None → 現在日時 |
| TestChatgptEmptyConversations | test_conversation_without_mapping | mapping なし → スキップ |
| TestChatgptEmptyConversations | test_conversation_without_id | id なし → スキップ |
| TestIdempotentExtractOpenai | test_existing_output_ignored | existing_output 無視、全処理 |
| TestIdempotentExtractOpenai | test_no_existing_output_arg | 引数なしで後方互換 |
| TestIdempotentExtractOpenai | test_empty_existing_output | 空 dict で全処理 |

## 実装ヒント

- `src/obsidian_etl/pipelines/extract_openai/nodes.py` に `parse_chatgpt_zip(partitioned_input: dict[str, Callable], existing_output: dict[str, Callable] | None = None) -> dict[str, dict]` を実装
- 既存の ChatGPT パーサー `src/etl/stages/extract/chatgpt_extractor.py` を参照
  - `traverse_messages()`: mapping tree → chronological messages (parent chain traversal)
  - `extract_text_from_parts()`: multimodal parts → text + placeholders
  - `convert_role()`: user→human, assistant→assistant, system/tool→None (excluded)
- `obsidian_etl.utils.chunker.should_chunk` / `split_messages` でチャンク分割
- `obsidian_etl.utils.file_id.generate_file_id` で SHA256 file_id 生成
- ZIP は `zipfile.ZipFile` + `io.BytesIO` で読み込み、conversations.json を抽出
- partitioned_input: 各キーは ZIP 名、値は `Callable[[], bytes]`（Kedro PartitionedDataset 形式）
- existing_output は後方互換のため引数に含めるが、parse 内では使用しない

## FAIL 出力例

```
ERROR: test_nodes (unittest.loader._FailedTest.test_nodes)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_nodes
Traceback (most recent call last):
  File "tests/pipelines/extract_openai/test_nodes.py", line 22, in <module>
    from obsidian_etl.pipelines.extract_openai.nodes import parse_chatgpt_zip
ImportError: cannot import name 'parse_chatgpt_zip' from 'obsidian_etl.pipelines.extract_openai.nodes'
```

## 既存テストへの影響

- pipelines テスト: 78 PASS + 1 ERROR (新規 extract_openai のみ)
- 既存テスト (Extract Claude: 21, Transform: 24, Organize: 32, Integration: 6, Hooks: 7, Pipeline Registry: 8) は全て PASS
