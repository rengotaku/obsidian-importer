# Phase 4 テストスケルトン作成完了

## Phase 4 - User Story 1 - ChatGPT チャンク対応

### サマリー
- Phase: Phase 4 - User Story 1
- 作成テスト: 2 ファイル、22 メソッド
- ステータス: ✅

### 作成ファイル
| ファイル | テストメソッド数 | 対象機能 |
|----------|-----------------|----------|
| src/etl/tests/test_stages.py | 8 | ChatGPTExtractor 抽象メソッド実装 |
| src/etl/tests/test_chunking_integration.py | 14 | チャンク処理統合テスト |

### テスト観点

#### test_stages.py (ChatGPTExtractor 抽象メソッド)
- 正常系: 4 メソッド
  - `_discover_raw_items()` の実装確認
  - `_build_conversation_for_chunking()` の実装確認
  - Iterator 返却の検証
  - ConversationProtocol 返却の検証
- エッジケース: 4 メソッド
  - チャンク処理の分離確認
  - 無効な ZIP ファイル処理
  - conversations.json 欠損処理
  - mapping → ConversationProtocol 変換

#### test_chunking_integration.py (統合テスト)
- ChatGPT チャンク処理: 6 メソッド
  - 大規模会話のチャンク分割
  - 小規模会話の非分割
  - チャンクメタデータの存在確認
  - チャンクコンテンツ構造の検証
  - オーバーラップメッセージの確認
  - チャンクインデックスの連番性
- 全 Extractor 統合テスト: 4 メソッド
  - Claude/ChatGPT/GitHub の抽象メソッド実装確認
  - 未実装時の TypeError 発生確認
- メタデータ伝播テスト: 4 メソッド
  - Extract/Transform/Load Stage でのメタデータ保持
  - pipeline_stages.jsonl への記録

### テスト設計原則

#### エッジケースの考慮
- 閾値境界 (25,000 文字ちょうど)
- 単一メッセージの超大規模会話
- 空の会話
- Unicode 文字列の処理

#### Template Method パターンの検証
- `_discover_raw_items()`: 生データの発見のみ (チャンク処理なし)
- `_build_conversation_for_chunking()`: プロバイダー固有の変換
- チャンク処理は BaseExtractor で自動適用

#### チャンクメタデータの追跡
- `is_chunked`: チャンク分割フラグ
- `parent_item_id`: 親アイテムの ID
- `chunk_index`: チャンクインデックス (0-based)
- `total_chunks`: 総チャンク数

### 次ステップ
phase-executor がテストの中身（assertions）を実装:
1. T033-T036: テスト実装 (RED)
2. T038-T041: ChatGPTExtractor 実装 (GREEN)
3. T042: 全テストパス検証
4. T043-T044: 検証とフェーズ出力

### 参照実装
- ClaudeExtractor (Phase 3 完了):
  - `_discover_raw_items()`: conversations.json パース
  - `_build_conversation_for_chunking()`: SimpleConversation 変換
  - `_chunk_if_needed()`: チャンク固有 JSON 生成 (override)

### 設計上の注意点
- ChatGPT の mapping 構造は Claude と異なる (ツリー走査が必要)
- ConversationProtocol への変換ロジックが重要
- ZIP ファイル処理のエラーハンドリング
- 既存の Step クラス (ReadZipStep, ParseConversationsStep など) との統合

### タスク更新
- tasks.md の T031, T032 を `[x]` に更新済み
