# Phase 5 テストスケルトン作成完了

**Feature**: 035-chunking-mixin
**Phase**: Phase 5 - User Story 2 - GitHub チャンク対応
**Task**: テスト設計 (T046)
**Date**: 2026-01-26
**Status**: ✅ COMPLETED

## サマリー

Phase 5 のテスト設計タスク (T046) を完了。GitHubExtractor の Template Method パターン準拠を検証するテストスケルトンを作成。

- **Phase**: Phase 5 - User Story 2
- **作成テスト**: 1 ファイル、6 メソッド
- **ステータス**: ✅

## 作成ファイル

| ファイル | テストメソッド数 | 対象機能 |
|----------|-----------------|----------|
| src/etl/tests/test_stages.py | 6 | GitHubExtractor 抽象メソッド実装検証 |

## テストメソッド詳細

### TestGitHubExtractorAbstractMethods

GitHubExtractor の Template Method パターン準拠を検証するテストクラス。

| テストメソッド | テスト観点 |
|---------------|----------|
| `test_github_extractor_discover_raw_items` | `_discover_raw_items()` メソッドが実装されていることを確認 |
| `test_github_extractor_build_conversation_returns_none` | `_build_conversation_for_chunking()` が None を返すことを確認 |
| `test_github_extractor_instantiation_succeeds` | TypeError なしでインスタンス化できることを確認 |
| `test_github_extractor_discover_raw_items_returns_iterator` | `_discover_raw_items()` が Iterator を返すことを確認 |
| `test_github_extractor_no_chunking_applied` | 大きなファイルでもチャンク処理をしないことを確認 |
| `test_github_extractor_existing_behavior_preserved` | 既存の動作を維持していることを確認 |

## テスト観点

### 正常系
- **抽象メソッド実装**: `_discover_raw_items()` と `_build_conversation_for_chunking()` の実装確認
- **インスタンス化**: TypeError が発生しないことの確認
- **Iterator 返却**: `_discover_raw_items()` が正しく Iterator を返すことの確認

### エッジケース
- **チャンクスキップ**: `_build_conversation_for_chunking()` が None を返し、チャンク処理がスキップされることの確認
- **大きなファイル**: 25,000文字超のファイルでもチャンク分割されないことの確認
- **既存動作維持**: リファクタリング後も既存のテストがパスすることの確認

## 設計方針

### Template Method パターン準拠

GitHubExtractor は GitHub の記事（Jekyll ブログ）を処理するため、チャンク分割は不要。

**実装方針**:
1. `_discover_raw_items()`: 既存の `discover_items()` ロジックをリネーム
2. `_build_conversation_for_chunking()`: 常に `None` を返却 (チャンク不要)

**チャンクスキップの理由**:
- GitHub 記事は構造化されたブログ投稿（1記事 = 1ファイル）
- 25,000文字を超える記事は稀
- 記事の途中で分割すると文脈が失われる
- ConversationProtocol には変換不要（会話形式ではない）

### 参照実装

**ClaudeExtractor** (Phase 3):
```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    # Parse conversations.json and yield items
    ...

def _build_conversation_for_chunking(self, item: ProcessingItem) -> ConversationProtocol:
    # Convert to ConversationProtocol
    return SimpleConversation(...)
```

**ChatGPTExtractor** (Phase 4):
```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    # Parse ZIP and yield expanded conversations
    ...

def _build_conversation_for_chunking(self, item: ProcessingItem) -> ChatGPTConversation:
    # Convert to ChatGPTConversation
    return ChatGPTConversation(...)
```

**GitHubExtractor** (Phase 5 - 実装予定):
```python
def _discover_raw_items(self, input_path: Path) -> Iterator[ProcessingItem]:
    # Clone repo and yield markdown files (既存ロジック)
    ...

def _build_conversation_for_chunking(self, item: ProcessingItem) -> None:
    # GitHub articles don't need chunking
    return None
```

## 次ステップ

### テスト実装 (RED)

Phase 5 の次のタスク:
- **T047**: `test_github_extractor_discover_raw_items` の assertions 実装
- **T048**: `test_github_extractor_build_conversation_returns_none` の assertions 実装
- **T049**: `make test` で新しいテストが FAIL することを確認 (RED)

### 実装 (GREEN)

- **T050**: `discover_items()` を `_discover_raw_items()` にリネーム
- **T051**: `_build_conversation_for_chunking()` を実装 (常に `None` 返却)
- **T052**: `make test` で全テストが PASS することを確認 (GREEN)

### 検証

- **T053**: 既存の GitHubExtractor テストがすべてパスすることを確認
- **T054**: Phase 5 出力ドキュメント生成

## ファイル配置

```
src/etl/tests/
└── test_stages.py         # GitHubExtractor テストスケルトン追加
    └── TestGitHubExtractorAbstractMethods (新規クラス)
        ├── test_github_extractor_discover_raw_items
        ├── test_github_extractor_build_conversation_returns_none
        ├── test_github_extractor_instantiation_succeeds
        ├── test_github_extractor_discover_raw_items_returns_iterator
        ├── test_github_extractor_no_chunking_applied
        └── test_github_extractor_existing_behavior_preserved
```

## 既存構造との整合性

### test_stages.py の構造

```python
# Abstract class tests
TestBaseStageAbstract
TestBaseStageImplementation
TestStageContext
TestBaseStep

# Concrete extractor tests
TestClaudeExtractorSteps
TestClaudeExtractorAbstractMethods (Phase 3)

TestChatGPTExtractorSteps
TestChatGPTExtractorAbstractMethods (Phase 4)

TestGitHubExtractorAbstractMethods (Phase 5 - 新規)
```

新しい `TestGitHubExtractorAbstractMethods` クラスは、Phase 3/4 で確立されたパターンに従っている。

## 成功時の出力

```markdown
## Phase 5 テストスケルトン作成完了

### サマリー
- Phase: Phase 5 - User Story 2
- 作成テスト: 1 ファイル、6 メソッド
- ステータス: ✅

### 作成ファイル
| ファイル | テストメソッド数 | 対象機能 |
|----------|-----------------|----------|
| test_stages.py | 6 | GitHubExtractor 抽象メソッド |

### テスト観点
- 正常系: 3
- エッジケース: 3

### 次ステップ
phase-executor がテストの中身（assertions）を実装
```

## Checkpoint

**Phase 5 テスト設計**: ✅ COMPLETED - テストスケルトン作成完了

**Status**: 次のタスク (T047-T049: テスト実装 RED) に進む準備完了

**Confidence**: HIGH - Phase 3/4 の確立されたパターンに従ったスケルトン作成
