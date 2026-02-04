# 030-chatgpt-import 要件チェックリスト

**Created**: 2026-01-22
**Status**: Draft

## Functional Requirements

| ID | 要件 | 状態 |
|----|------|------|
| FR-001 | ZIP ファイルを展開して `conversations.json` を読み取る | [ ] |
| FR-002 | `mapping` ツリー構造をフラットなメッセージリストに変換する | [ ] |
| FR-003 | Unix timestamp を `YYYY-MM-DD` 形式に変換する | [ ] |
| FR-004 | `source_provider: openai` を frontmatter に設定する | [ ] |
| FR-005 | 既存の Transform/Load ステージを再利用する | [ ] |
| FR-006 | `--provider` オプションで Claude/ChatGPT を切り替え可能にする | [ ] |
| FR-007 | メッセージ数が MIN_MESSAGES 未満の会話をスキップする | [ ] |
| FR-008 | file_id で重複を検出し、上書きする | [ ] |
| FR-009 | system ロールのメッセージを出力から除外する | [ ] |
| FR-010 | マルチモーダルコンテンツ（画像等）をプレースホルダーとして処理する | [ ] |

## Non-Functional Requirements

| ID | 要件 | 状態 |
|----|------|------|
| NFR-001 | 1295 会話のインポートが 2 時間以内に完了する | [ ] |
| NFR-002 | 既存の Claude インポートテストが引き続きパスする | [ ] |
| NFR-003 | ZIP 展開は一時ディレクトリで行い、処理後に削除する | [ ] |

## User Stories

| Priority | Story | 状態 |
|----------|-------|------|
| P1 | 基本インポート - ZIP から Markdown 生成 | [ ] |
| P1 | メタデータ抽出 - title, summary, tags, created | [ ] |
| P2 | 既存パイプライン統合 - --provider オプション | [ ] |
| P2 | 短い会話のスキップ | [ ] |
| P2 | 重複検出 - file_id ベース | [ ] |
| P3 | 添付ファイル処理 - プレースホルダー | [ ] |

## Success Criteria

| ID | 基準 | 状態 |
|----|------|------|
| SC-001 | ChatGPT ZIP からの会話インポート成功率 95% 以上 | [ ] |
| SC-002 | 生成された Markdown が Obsidian で正常に表示される | [ ] |
| SC-003 | frontmatter に必須フィールドが含まれる | [ ] |
| SC-004 | 既存の Claude インポートテストが 100% パスする | [ ] |
| SC-005 | `make import INPUT=... PROVIDER=openai` で CLI から実行可能 | [ ] |

## Edge Cases

| ケース | 状態 |
|--------|------|
| 空の conversations.json | [ ] |
| 破損した ZIP ファイル | [ ] |
| 超長い会話（チャンク分割） | [ ] |
| マルチモーダルコンテンツ | [ ] |
| system メッセージ | [ ] |
| タイムスタンプなし | [ ] |
| 会話タイトルなし | [ ] |

## テスト項目

| テスト | 状態 |
|--------|------|
| ユニットテスト: ChatGPTExtractor | [ ] |
| ユニットテスト: traverse_messages | [ ] |
| ユニットテスト: timestamp 変換 | [ ] |
| 統合テスト: ZIP → Markdown パイプライン | [ ] |
| 統合テスト: --provider オプション | [ ] |
| 回帰テスト: Claude インポート | [ ] |
