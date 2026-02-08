# Phase 7 Output

## 作業概要
- Phase 7 - US3 OpenAI (ChatGPT) プロバイダーの実装完了
- FAIL テスト 35 件を PASS させた
- parse_chatgpt_zip ノード実装: ZIP 展開 → mapping tree 走査 → multimodal 処理 → チャンク分割
- import_openai パイプライン登録: extract_openai + transform + organize の一気通貫

## 修正ファイル一覧

### 実装ファイル

- `src/obsidian_etl/pipelines/extract_openai/nodes.py` - parse_chatgpt_zip ノード実装 (370行)
  - `parse_chatgpt_zip(partitioned_input, params, existing_output)`: ZIP → ParsedItem dict
  - `_extract_conversations_from_zip()`: ZIP から conversations.json 抽出
  - `_traverse_messages()`: ChatGPT mapping tree → chronological messages (parent chain 走査)
  - `_convert_role()`: user→human, assistant→assistant, system/tool→None (除外)
  - `_extract_text_from_parts()`: multimodal parts → text + placeholders
    - `image_asset_pointer` → `[Image: asset_pointer]`
    - `audio_asset_pointer` → `[Audio: filename]`
  - `_format_conversation_content()`: messages → "Human:/.../Assistant:..." 形式
  - `_fallback_conversation_name()`: title=None → 最初のユーザーメッセージ (50文字)
  - `_convert_timestamp()`: Unix timestamp → ISO 8601
  - チャンク分割: `should_chunk()` / `split_messages()` (25000+ chars)
  - existing_output 引数: 後方互換のみ (Resume ロジックは Transform で実施)

- `src/obsidian_etl/pipelines/extract_openai/pipeline.py` - OpenAI Extract パイプライン定義
  - `create_pipeline()`: parse_chatgpt_zip ノードで raw_openai_conversations → parsed_items

- `src/obsidian_etl/pipeline_registry.py` - import_openai パイプライン登録
  - `import_openai`: extract_openai + transform + organize
  - import_claude と同じ Transform / Organize パイプラインを再利用

### テスト結果

```
$ python -m unittest tests.pipelines.extract_openai.test_nodes -v

----------------------------------------------------------------------
Ran 35 tests in 0.006s

OK
```

**テスト内訳**:
- TestParseChatgptZipBasic: 8 テスト (基本構造、ゴールデンデータ一致)
- TestChatgptTreeTraversal: 3 テスト (線形/分岐ツリー走査、system ノード除外)
- TestChatgptMultimodal: 3 テスト (画像/音声プレースホルダー、混在処理)
- TestChatgptRoleConversion: 5 テスト (user→human, system/tool 除外)
- TestChatgptChunking: 6 テスト (25000+ chars → 複数チャンク、メタデータ検証)
- TestChatgptEmptyConversations: 7 テスト (空 ZIP、短い会話スキップ、フォールバック)
- TestIdempotentExtractOpenai: 3 テスト (existing_output 無視、後方互換性)

### リグレッション確認

```
$ python -m unittest discover -s tests/pipelines -p "test_*.py" -v

----------------------------------------------------------------------
Ran 112 tests in 0.013s

OK
```

Phase 2-6 の全テスト (Extract Claude: 21, Transform: 24, Organize: 32, Idempotent: 11) + Phase 7 (Extract OpenAI: 35) = 112 テスト全て PASS。

```
$ python -m unittest tests.test_hooks tests.test_pipeline_registry tests.test_integration -v

----------------------------------------------------------------------
Ran 21 tests in 0.410s

OK
```

Hooks (7 テスト), Pipeline Registry (8 テスト), Integration (6 テスト) も全て PASS。リグレッションなし。

## 実装の詳細

### ChatGPT 固有処理

#### 1. Mapping Tree 走査

ChatGPT の会話は mapping tree 構造 (node_id → {message, parent, children}) で保存される。
`current_node` から parent chain を辿り、chronological order に変換:

```python
def _traverse_messages(mapping, current_node):
    raw_messages = []
    node_id = current_node

    # Traverse parent chain
    while node_id:
        node = mapping.get(node_id, {})
        if node.get("message"):
            raw_messages.append(node["message"])
        node_id = node.get("parent")

    # Reverse to chronological order (oldest first)
    raw_messages.reverse()
```

分岐ツリーの場合、`current_node` から辿ったパスのみを使用 (side branch は除外)。

#### 2. Multimodal 処理

`content.parts` 配列に text (str) と non-text (dict) が混在:

```python
def _extract_text_from_parts(parts):
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict):
            if part.get("content_type") == "image_asset_pointer":
                text_parts.append(f"[Image: {part['asset_pointer']}]")
            elif "audio" in part.get("content_type", "").lower():
                text_parts.append(f"[Audio: {part.get('filename', 'unknown')}]")
```

#### 3. Role 変換

- `user` → `human`
- `assistant` → `assistant` (維持)
- `system`, `tool` → None (除外)

#### 4. Timestamp 変換

Unix timestamp → ISO 8601:

```python
def _convert_timestamp(ts):
    if ts is None:
        dt = datetime.now(tz=UTC)  # Fallback
    else:
        dt = datetime.fromtimestamp(ts, tz=UTC)
    return dt.isoformat()
```

#### 5. チャンク分割

Claude Extract と同じロジック (`should_chunk()` / `split_messages()`) を共有。
25000+ chars で分割、chunk metadata (is_chunked, chunk_index, total_chunks, parent_item_id) 設定。

### 共通パイプライン再利用

Transform / Organize パイプラインは Claude と OpenAI で共有:

- **extract_knowledge**: LLM 知識抽出 (プロバイダー非依存)
- **generate_metadata**: メタデータ生成 (source_provider="openai" のみ差異)
- **format_markdown**: Markdown フォーマット (共通)
- **classify_genre**: ジャンル判定 (共通)
- **move_to_vault**: Vault 配置 (共通)

### 後方互換性

`existing_output` 引数は Phase 6 の Resume パターンに合わせて定義したが、Parse stage では使用しない:

- Extract stage: 常に全 conversation を処理 (skip なし)
- Transform stage: existing_output で LLM 呼び出しをスキップ (Resume 実現)

## 次 Phase への引き継ぎ

### Phase 8 (US4 GitHub Jekyll プロバイダー) で必要な情報

- **Extract パターン**: OpenAI と同じパターンで実装可能
  - `parse_github_jekyll(partitioned_input, params, existing_output)`: git clone → frontmatter 変換 → ParsedItem
  - existing_output は後方互換のみ (使用しない)

- **Catalog 設定**: GitHub 用の raw_github_posts データセット追加
  - PartitionedDataset で Markdown ファイルを読み込み

- **Transform / Organize**: 共通パイプライン再利用 (3 プロバイダー間で共有)

### 技術的注意点

- **Mapping tree 走査**: current_node から parent chain を辿る (DFS ではない)
- **Multimodal**: dict の `content_type` フィールドで判定
- **Chunking**: Claude と同じロジック (`obsidian_etl.utils.chunker`) を共有
- **Role conversion**: user→human 変換を忘れないこと (Claude は sender="human" だが ChatGPT は role="user")

## 実装のミス・課題

### 初回実装での注意点

**症状**: `_extract_text_from_parts()` で text parts を `\n` で join していた

**原因**: ChatGPT の parts は同一メッセージ内の断片のため、改行で区切ると読みにくい

**修正**: `"\n".join(text_parts)` で結合 (各 part を新しい行に配置)

**学び**: Multimodal content は text + non-text が混在するため、適切な separator が必要

### 現時点での課題

なし。全テスト PASS。Phase 7 完了。
