# Research: LLMインポート エラーデバッグ改善

## 1. 現状分析

### 現在のフォルダ構造

```
@llm_exports/claude/
├── data-*/               # 元データ（conversations.json等）
├── parsed/conversations/ # Phase 1出力（全セッション共有）
└── .extraction_state.json

@plan/
├── import_YYYYMMDD_HHMMSS/  # セッションログ
└── test_YYYYMMDD_HHMMSS/    # テストログ

@index/                   # Phase 2出力（最終出力先）
```

### 問題点

1. **エラーデバッグ困難**: エラー時にLLM出力が保存されない
2. **中間ファイル消失**: Phase 1出力は処理後に削除される
3. **フォルダ混在**: import_*, test_* が同階層に並ぶ
4. **セッション追跡困難**: 成果物が分散している

## 2. 設計決定

### Decision 1: エラー詳細ファイルフォーマット

**選択**: Markdown形式

**理由**:
- Obsidian で直接閲覧可能
- 構造化情報と長文テキストの両方を扱える
- 既存のノートと一貫性がある

**代替案検討**:
- JSON: 機械処理しやすいが可読性低
- YAML: フロントマター形式と混同する可能性

### Decision 2: フォルダ階層

**選択**: `@plan/{type}/{session_id}/` 形式

**理由**:
- 種別でグルーピング（import/organize/test）
- セッション単位で全成果物を集約
- 削除・移動が容易

**代替案検討**:
- `@plan/{session_id}/{type}/`: セッションが先 → 種別での一覧性が低下
- フラット構造維持: 既存問題が解決しない

### Decision 3: 中間ファイルの扱い

**選択**: セッションフォルダ内に保持、自動削除しない

**理由**:
- デバッグ時に全段階の出力を確認可能
- クリーンアップで一括削除可能
- ディスク使用量はクリーンアップで管理

**代替案検討**:
- 即時削除（現行）: デバッグ不可
- 成功時のみ削除: 部分的改善だが不十分

### Decision 4: クリーンアップ戦略

**選択**: 日数ベース + エラー保護オプション

**理由**:
- シンプルで予測可能
- エラー情報の保護が可能
- プレビューモードで安全確認

**代替案検討**:
- サイズベース: 計算コスト高、予測困難
- 手動のみ: 自動化のメリット消失

## 3. 実装方針

### エラー詳細ファイル構造

```markdown
# Error Detail: {conversation_title}

**Session**: {session_id}
**Conversation ID**: {conversation_id}
**Timestamp**: {timestamp}
**Error Type**: {error_type}
**Error Position**: {position}

## Error Message

{error_message}

## Original Content (Source)

```text
{original_conversation_content}
```

## LLM Prompt

```text
{llm_prompt}
```

## LLM Raw Output

```text
{llm_raw_output}
```

## Context

{context_around_error}
```

### SessionLogger 変更点

1. `session_dir` を `@plan/{type}/{session_id}/` に変更
2. `parsed/` サブフォルダを作成
3. `output/` サブフォルダを作成
4. `errors/` サブフォルダを作成

### cli.py 変更点

1. Phase 1出力先: `session_dir/parsed/conversations/`
2. Phase 2出力先: `session_dir/output/` → 成功時に `@index/` へコピー
3. エラー時: `session_dir/errors/` に詳細ファイル出力
4. 中間ファイル削除ロジック削除

## 4. リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| ディスク使用量増加 | 中 | クリーンアップ機能で管理 |
| 既存セッションとの非互換 | 低 | マイグレーションコマンド提供 |
| パフォーマンス低下 | 低 | ファイルコピーは軽量 |

## 5. 依存関係

- `llm_import/common/session_logger.py`: 既存、修正必要
- `llm_import/common/knowledge_extractor.py`: 既存、エラー情報取得
- `llm_import/cli.py`: 既存、フロー修正
