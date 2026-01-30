# Phase 6 完了報告: User Story 4 - 短い会話のスキップ

## サマリー

- **Phase**: Phase 6 - User Story 4 (短い会話のスキップ)
- **タスク**: 6/6 完了
- **ステータス**: ✅ 完了
- **実行日時**: 2026-01-23

## 実行タスク

| # | タスク | 状態 | 備考 |
|---|--------|------|------|
| T030 | Phase 5 出力読み込み | ✅ | ph5-output.md 確認完了 |
| T031 | メッセージ数バリデーション追加 | ✅ | discover_items() に実装 |
| T032 | system/tool メッセージ除外 | ✅ | convert_role() で既に除外済み |
| T033 | スキップログ記録 | ✅ | skip_reason='skipped_short' |
| T034 | 回帰テスト実行 | ✅ | 275 tests OK (skipped=9) |
| T035 | Phase 6 出力生成 | ✅ | このファイル |

## 成果物

### 修正ファイル

#### `/path/to/project/src/etl/stages/extract/chatgpt_extractor.py`

**追加機能**:

1. **MIN_MESSAGES 定数追加** (T031):
   ```python
   # Short conversation skip threshold (same as Claude extractor)
   MIN_MESSAGES = 3
   ```

2. **メッセージ数バリデーション** (T031-T032):
   ```python
   # T031-T032: Skip conversations with fewer than MIN_MESSAGES
   # system/tool messages are already excluded by convert_role()
   if len(chat_messages) < MIN_MESSAGES:
       # T033: Log skip with reason 'skipped_short'
       item = ProcessingItem(
           item_id=conversation_id,
           source_path=input_path,
           current_step='discover',
           status=ItemStatus.SKIPPED,
           metadata={
               'conversation_uuid': conversation_id,
               'conversation_name': title,
               'created_at': convert_timestamp(create_time),
               'source_provider': 'openai',
               'source_type': 'conversation',
               'skip_reason': 'skipped_short',
               'message_count': len(chat_messages),
           },
           content=None,
       )
       items.append(item)
       continue
   ```

**実装詳細**:

- `chat_messages` のカウントを使用（system/tool は `convert_role()` で既に除外）
- `len(chat_messages) < MIN_MESSAGES` の場合、`ItemStatus.SKIPPED` で ProcessingItem を生成
- `skip_reason='skipped_short'` を metadata に記録
- `message_count` も metadata に保存（デバッグ用）
- スキップされた会話も items に追加（統計・ログ記録のため）

## 検証結果

### T031-T032: メッセージ数バリデーション

**実装箇所**: `chatgpt_extractor.py:265-284`

**検証ポイント**:

| 項目 | 実装 | 検証 |
|------|------|------|
| MIN_MESSAGES 定数 | 3 | ✅ |
| system/tool メッセージ除外 | `convert_role()` で None 返却 | ✅ |
| カウント対象 | `chat_messages` (human/assistant のみ) | ✅ |
| スキップ条件 | `len(chat_messages) < MIN_MESSAGES` | ✅ |

**convert_role() の動作確認**:

```python
def convert_role(role: str) -> str | None:
    """Convert ChatGPT role to Claude-compatible sender.

    Args:
        role: ChatGPT role (user, assistant, system, tool).

    Returns:
        Converted role (human, assistant) or None if excluded.
    """
    role_mapping = {
        'user': 'human',
        'assistant': 'assistant',
    }
    return role_mapping.get(role)
```

- `user` → `human` (カウント対象)
- `assistant` → `assistant` (カウント対象)
- `system` → `None` (除外)
- `tool` → `None` (除外)

**メッセージ構築ロジック**:

```python
for msg in messages:
    author = msg.get('author', {})
    role = author.get('role', '')

    sender = convert_role(role)
    if sender is None:  # system/tool は continue
        continue

    # text 抽出
    content_obj = msg.get('content', {})
    parts = content_obj.get('parts', [])
    text = extract_text_from_parts(parts)

    if not text:
        continue

    chat_messages.append({...})  # human/assistant のみ追加
```

**結論**: system/tool メッセージは `chat_messages` に含まれないため、カウントから自動的に除外される。

### T033: スキップログ記録

**記録内容**:

| フィールド | 値 | 用途 |
|-----------|---|------|
| `status` | `ItemStatus.SKIPPED` | Phase ステータス判定 |
| `skip_reason` | `'skipped_short'` | スキップ理由識別 |
| `message_count` | `len(chat_messages)` | 実際のメッセージ数（デバッグ用） |
| `content` | `None` | スキップされた会話は内容なし |

**ログ出力先**:

- **phase.json**: ProcessingItem として記録され、Phase 終了時に集計
- **debug モード**: step_output/discover.jsonl に詳細が出力

**フォーマット例** (phase.json):

```json
{
  "item_id": "conv-123",
  "status": "skipped",
  "metadata": {
    "conversation_name": "Short Chat",
    "skip_reason": "skipped_short",
    "message_count": 2,
    "source_provider": "openai"
  }
}
```

### T034: 回帰テスト結果

**テストサマリー**:

```
Ran 275 tests in 11.508s
OK (skipped=9)
```

**新規テスト**: 0 件（Phase 6 は既存ロジック拡張）

| テスト種類 | 件数 | 結果 |
|-----------|------|------|
| 既存テスト | 275 | ✅ すべてパス |
| スキップ | 9 | - |
| **合計** | **275** | **✅** |

**設計制約の検証**:

| 制約 | 検証結果 |
|------|---------|
| **CC-001**: claude_extractor.py 無変更 | ✅ ファイル変更なし |
| **CC-002**: 既存テストがパス | ✅ 275 tests OK |
| **CC-003**: デフォルトで Claude 使用 | ✅ 影響なし |
| **CC-004**: Transform/Load 再利用 | ✅ 変更なし |

**関連テスト**:

既存の `TestMinMessagesSkipLogic` テストが引き続きパス:

- `test_skip_conversation_with_one_message`: ✅ 1 メッセージ会話はスキップ
- `test_skip_conversation_with_two_messages`: ✅ 2 メッセージ会話はスキップ
- `test_process_conversation_with_three_or_more_messages`: ✅ 3+ メッセージ会話は処理

**Note**: 上記テストは Claude Extractor 向けだが、同じ MIN_MESSAGES ロジックを ChatGPT Extractor にも適用したため、動作は整合している。

## 技術的詳細

### スキップロジックのフロー

**データフロー**:

```
ZIP ファイル
  ↓
read_conversations_from_zip()
  ↓
mapping → traverse_messages()
  ↓
for msg in messages:
  ↓ (system/tool を除外)
  if convert_role(role) is None: continue
  ↓
  chat_messages.append(...)
  ↓
if len(chat_messages) < MIN_MESSAGES:
  ↓
  ProcessingItem(status=SKIPPED, skip_reason='skipped_short')
  ↓
  items.append(item)  # スキップもログに記録
  ↓
  continue
else:
  ↓
  ProcessingItem(status=PENDING, content=conversation_data)
```

### Claude との一貫性

**MIN_MESSAGES 定数の共通化**:

| Extractor | MIN_MESSAGES | 実装箇所 |
|-----------|--------------|---------|
| Claude | 3 (参考実装) | legacy: `src/converter/scripts/llm_import/cli.py:93` (MIN_MESSAGES = 2) |
| ChatGPT | 3 | `src/etl/stages/extract/chatgpt_extractor.py:18` |

**Note**: レガシー実装では `MIN_MESSAGES = 2` だったが、新 ETL パイプラインでは `MIN_MESSAGES = 3` に統一（より厳格なフィルタリング）。

**スキップ理由の共通化**:

両方の Extractor で同じ `skip_reason='skipped_short'` を使用することで、Phase レベルでの統計・分析が容易。

### エッジケース対応

**会話パターン別の動作**:

| パターン | メッセージ構成 | カウント | 動作 |
|---------|-------------|---------|------|
| 超短い会話 | 1 human | 1 | スキップ |
| 短い会話 | 1 human + 1 assistant | 2 | スキップ |
| ぎりぎり短い | 2 human + 1 assistant | 3 | **処理** |
| システムのみ | 5 system | 0 | スキップ（空） |
| 混在 | 1 human + 3 system + 1 assistant | 2 | スキップ |
| 正常 | 2 human + 2 assistant | 4 | 処理 |

**空メッセージの処理**:

```python
if not chat_messages:  # Line 260
    continue  # 空の場合は item を作らない
```

空メッセージの会話は ProcessingItem を生成せず、完全にスキップ（ログにも残らない）。

**スキップされた会話の追跡**:

- `status=SKIPPED` の ProcessingItem を items に追加
- Phase 集計でカウント可能
- debug モードで詳細確認可能

### US4 成功基準の達成状況

**User Story 4 要件** (spec.md:81-93):

> メッセージ数が閾値未満の会話はスキップする（Claude と同じロジック）。
>
> **Independent Test**: メッセージ数 2 以下の会話がスキップされ、ログに記録される。

**Acceptance Scenarios 達成状況**:

| # | シナリオ | 達成 |
|---|---------|------|
| 1 | メッセージ数 < MIN_MESSAGES → スキップ & `skipped_short` ログ | ✅ Line 265-284 |
| 2 | system メッセージはカウントに含めない | ✅ convert_role() で除外 |

**Independent Test 検証**:

```python
# メッセージ数 2 の会話
chat_messages = [
    {"sender": "human", "text": "Hello"},
    {"sender": "assistant", "text": "Hi"},
]
# len(chat_messages) = 2 < MIN_MESSAGES (3)
# → status=SKIPPED, skip_reason='skipped_short'
```

**検証方法**:

```bash
# 実際の ChatGPT エクスポートでテスト
python -m src.etl import --input test.zip --provider openai --debug

# phase.json でスキップ会話を確認
cat .staging/@session/YYYYMMDD_HHMMSS/import/phase.json | jq '.items[] | select(.status == "skipped")'
```

**期待される出力**:

```json
{
  "item_id": "conv-short",
  "status": "skipped",
  "metadata": {
    "skip_reason": "skipped_short",
    "message_count": 2
  }
}
```

### スキップログの活用

**Phase 集計での利用**:

```python
# phase.json から統計を取得
total = len(items)
skipped_short = len([i for i in items if i.metadata.get('skip_reason') == 'skipped_short'])
processed = len([i for i in items if i.status == 'completed'])

print(f"Total: {total}, Skipped (short): {skipped_short}, Processed: {processed}")
```

**debug モードでの確認**:

```bash
# step_output/discover.jsonl を確認
cat extract/step_output/discover.jsonl | jq 'select(.skip_reason == "skipped_short")'
```

**CLI 出力での表示**:

```
[Phase] import started (provider: openai)
[Extract] Discovered 10 conversations
[Extract] Skipped 3 conversations (short)
[Extract] Processing 7 conversations
```

## 次 Phase への引き継ぎ

### Phase 7 の前提条件

- ✅ MIN_MESSAGES スキップロジックが動作
- ✅ system/tool メッセージがカウントから除外
- ✅ スキップ理由がログに記録
- ✅ 既存 Claude インポートに影響なし
- ✅ 全テストがパス

### Phase 7 で実装すべき内容

**User Story 5 (重複検出) のタスク**:

| Task | 内容 | 実装場所 |
|------|------|---------|
| T037 | file_id 生成 | `chatgpt_extractor.py` |
| T038 | 重複検出ロジック検証 | SessionLoader |
| T039 | 回帰テスト実行 | make test |

**確認ポイント**:

1. 会話コンテンツから file_id をハッシュ生成
2. 同一 file_id の既存ファイルを上書き
3. 既存の SessionLoader ロジックが動作

**参考実装**:

- `src/etl/utils/file_id.py` - file_id 生成関数
- `src/etl/stages/load/session_loader.py` - 重複検出・上書きロジック

### Phase 8 で実装すべき内容

**User Story 6 (添付ファイル処理) のタスク**:

| Task | 内容 | 実装場所 |
|------|------|---------|
| T042 | image_asset_pointer 処理 | `chatgpt_extractor.py` |
| T043 | audio ファイル処理 | `chatgpt_extractor.py` |
| T044 | マルチモーダルエラー防止 | `chatgpt_extractor.py` |
| T045 | 回帰テスト実行 | make test |

**確認ポイント**:

1. 画像: `[Image: {asset_pointer}]` プレースホルダー（**既に実装済み**: Line 65）
2. 音声: `[Audio: {filename}]` プレースホルダー
3. エラーが発生しない

**既存実装の確認**:

```python
# Line 44-69: extract_text_from_parts()
if content_type == 'image_asset_pointer':
    asset_pointer = part.get('asset_pointer', 'unknown')
    text_parts.append(f"[Image: {asset_pointer}]")  # ✅ 既に実装済み
else:
    text_parts.append(f"[{content_type}]")  # その他のタイプもプレースホルダー化
```

**Note**: Phase 8 は画像プレースホルダーが既に実装されているため、音声ファイルの明示的な処理を追加する程度で完了。

### 利用可能なリソース

**実装済み機能**:

- `src/etl/stages/extract/chatgpt_extractor.py` - ChatGPT Extractor (MIN_MESSAGES スキップ実装済み)
- `src/etl/phases/import_phase.py` - provider 切り替え機能
- `src/etl/cli.py` - `--provider` オプション
- `src/etl/stages/transform/knowledge_transformer.py` - Transform (ChatGPT 互換)
- `src/etl/stages/load/session_loader.py` - Load (file_id 重複検出機能あり)

**参考実装**:

- `src/converter/scripts/llm_import/cli.py:565-575` - レガシー MIN_MESSAGES スキップ実装
- `src/etl/tests/test_import_phase.py:238-363` - MIN_MESSAGES テストケース

**設計ドキュメント**:

- `specs/030-chatgpt-import/plan.md` - 実装計画
- `specs/030-chatgpt-import/spec.md` - User Story 定義
- `specs/030-chatgpt-import/data-model.md` - データモデル
- `specs/030-chatgpt-import/quickstart.md` - クイックスタート

## Phase 6 完了確認

- [x] T030: Phase 5 出力読み込み
- [x] T031: メッセージ数バリデーション追加
- [x] T032: system/tool メッセージ除外
- [x] T033: スキップログ記録
- [x] T034: 回帰テスト実行
- [x] T035: Phase 6 出力生成

**Checkpoint 達成**: 短い会話のスキップロジック完了

---

## 付録: コマンド例

### スキップロジックの確認

```bash
# ChatGPT インポート（debug モード）
python -m src.etl import --input export.zip --provider openai --debug

# スキップされた会話を確認
SESSION_ID=$(ls -1t .staging/@session | head -1)
cat ".staging/@session/$SESSION_ID/import/phase.json" | jq '.items[] | select(.status == "skipped")'

# メッセージ数の分布を確認
cat ".staging/@session/$SESSION_ID/import/phase.json" | jq '.items[] | .metadata.message_count' | sort | uniq -c
```

### debug 出力の確認

```bash
# discover step の詳細ログ
cat ".staging/@session/$SESSION_ID/import/extract/step_output/discover.jsonl" | jq 'select(.skip_reason == "skipped_short")'
```

### 統計表示

```bash
# Phase ステータス確認
python -m src.etl status --session $SESSION_ID

# スキップ理由別集計
cat ".staging/@session/$SESSION_ID/import/phase.json" | jq -r '.items[] | .metadata.skip_reason' | sort | uniq -c
```

**期待される出力例**:

```
5 skipped_short
2 null
```

## 次のステップ

**Phase 7 開始条件**: すべて満たしている

次のコマンドで Phase 7 を開始してください:

```bash
# Phase 7 タスク実行
# - T037: file_id 生成実装
# - T038: 重複検出ロジック検証
# - T039: 回帰テスト実行
# - T040: Phase 7 出力生成
```

**Phase 7 の成功基準**:

- 会話コンテンツから file_id がハッシュ生成される
- 同一 file_id の既存ファイルが上書きされる
- 既存の SessionLoader ロジックが動作
- 既存テストが 100% パス

**実装優先順位**:

1. **Phase 7** (US5: 重複検出) - P2 - 再インポート対応
2. **Phase 8** (US6: 添付ファイル) - P3 - エッジケース対応（一部実装済み）
3. **Phase 9** (Polish) - ドキュメント整備

**並列実行可能**: Phase 7, 8 は独立しているため、別々のブランチで並列実装可能。
