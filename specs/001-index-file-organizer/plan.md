# Implementation Plan: Index File Organizer

**Feature Branch**: `001-index-file-organizer`
**Spec**: [spec.md](./spec.md)
**Status**: 計画策定中

---

## Executive Summary

`@index/` 内の未整理ファイルを Ollama で分類・正規化し、適切な Vault に自動配置するシステム。

**アーキテクチャ決定**:
- Claude Code: スクリプト起動 + 結果表示のみ（トークン節約）
- Python Script: オーケストレーター（ファイル操作、API呼び出し）
- Ollama (`gpt-oss:20b`): コンテンツ処理（分類、正規化）

---

## Phase 1: P1 - 単一ファイル整理機能

**目標**: 1つのファイルを完全に処理できる基盤を構築

### Task 1.1: スクリプト基盤作成

**ファイル**: `.claude/scripts/ollama_normalizer.py`

**機能**:
- コマンドライン引数解析（ファイルパス指定）
- ファイル読み込み・書き込み
- Ollama API 呼び出し基盤
- JSON 結果出力

**既存資産からの流用**:
- `ollama_genre_classifier.py` の Ollama 通信部分
- プログレスバー、エラーハンドリング

### Task 1.2: Ollama プロンプト設計

**入力**: ファイル名 + 内容（最大 4000 文字）

**出力 JSON 形式**:
```json
{
  "genre": "エンジニア|ビジネス|経済|日常|その他|dust",
  "confidence": 0.0-1.0,
  "is_dust": false,
  "dust_reason": null,
  "related_keywords": ["keyword1", "keyword2"],
  "frontmatter": {
    "title": "タイトル",
    "tags": ["tag1", "tag2"],
    "created": "YYYY-MM-DD"
  },
  "normalized_content": "整形済み本文..."
}
```

**プロンプト要件**:
- 6 ジャンル判定（その他、dust 含む）
- 関連キーワード抽出（3-5 個）
- Obsidian 規約に準拠した frontmatter 生成
- 本文整形（余分な空行削除、見出し整理）

### Task 1.3: ファイル移動ロジック

**処理フロー**:
```
1. ジャンル判定結果を取得
2. genre == "dust" → @dust/ へ移動
3. confidence < 0.7 → 要確認としてスキップ
4. related_keywords → 既存ファイル名マッチング → related 生成
5. 正規化ファイルを Vault へ移動
6. 元ファイル削除
```

**重複ファイル処理**:
- 同名ファイル存在時: `Title_1.md`, `Title_2.md` 形式で番号付与

### Task 1.4: 結果出力形式

**成功時**:
```
✅ ファイル整理完了
  📄 元ファイル: @index/AWS IAMの基礎.md
  📂 移動先: エンジニア/AWS/AWS IAMの基礎.md
  🏷️ ジャンル: エンジニア (confidence: 0.92)
  🔗 関連: [[AWS入門]], [[IAMポリシー設計]]
```

**dust 判定時**:
```
🗑️ Dust 判定
  📄 ファイル: @index/テスト.md
  📂 移動先: @dust/テスト.md
  📝 理由: テスト投稿、意味のある内容なし
```

---

## Phase 2: P2 - 複数ファイル一括整理

**目標**: バッチ処理と確認フローの実装

### Task 2.1: バッチ処理モード

**機能**:
- `@index/*.md` 全ファイル検出
- 除外パターン: `@index/claude/**`, `*.csv`, `*.md`（管理ファイル）
- 並列処理（Ollama API 負荷を考慮して逐次実行）

### Task 2.2: 確認プロンプト

**10 ファイル以上の場合**:
```
⚠️ 15 個のファイルを処理します
続行しますか？ (y/n/preview):
  y: 実行
  n: キャンセル
  preview: 処理内容をプレビュー
```

### Task 2.3: エラーハンドリング

**継続処理**:
- 1 ファイル失敗しても残りは継続
- 最後にエラーサマリー表示

**結果レポート**:
```
📊 処理結果サマリー
  ✅ 成功: 12 ファイル
  🗑️ Dust: 2 ファイル
  ⏭️ スキップ: 1 ファイル（要確認）
  ❌ エラー: 0 ファイル

詳細は @index/処理結果_2026-01-09.json を参照
```

---

## Phase 3: P3 - プレビューモード

**目標**: 安全な事前確認機能の実装

### Task 3.1: プレビュー生成

**コマンド**:
```bash
python ollama_normalizer.py --preview
```

**出力**:
```
📋 整理プレビュー

1. AWS IAMの基礎.md
   現在: @index/
   移動先: エンジニア/AWS/
   ジャンル: エンジニア (0.92)
   アクション: [承認] [変更] [スキップ]

2. テスト投稿.md
   現在: @index/
   移動先: @dust/
   理由: 意味のある内容なし
   アクション: [承認] [変更] [スキップ]
```

### Task 3.2: インタラクティブ修正

**変更オプション**:
- ジャンル手動指定
- 移動先フォルダ変更
- スキップ（後で処理）

---

## File Structure

```
.claude/scripts/
├── ollama_normalizer.py     # メインスクリプト（新規）
├── ollama_genre_classifier.py  # 既存（参考用）
└── normalize_obsidian.py    # 既存（参考用）

@index/
├── *.md                     # 整理対象ファイル
├── claude/                  # 除外（Claudeエクスポート専用）
└── 処理結果_YYYY-MM-DD.json # 処理ログ

@dust/                       # 新規作成（dust判定ファイル格納）
└── *.md
```

---

## Implementation Order

| 順序 | タスク | 依存 | 見積工数 |
|-----|-------|-----|---------|
| 1 | Task 1.1: スクリプト基盤 | なし | 小 |
| 2 | Task 1.2: Ollama プロンプト | 1.1 | 中 |
| 3 | Task 1.3: 移動ロジック | 1.2 | 小 |
| 4 | Task 1.4: 結果出力 | 1.3 | 小 |
| 5 | Task 2.1: バッチ処理 | 1.* | 小 |
| 6 | Task 2.2: 確認プロンプト | 2.1 | 小 |
| 7 | Task 2.3: エラーハンドリング | 2.1 | 小 |
| 8 | Task 3.1: プレビュー生成 | 2.* | 中 |
| 9 | Task 3.2: インタラクティブ修正 | 3.1 | 中 |

---

## Testing Strategy

### Unit Tests

```python
# tests/test_normalizer.py
def test_genre_classification():
    """ジャンル判定の正確性"""

def test_frontmatter_generation():
    """frontmatter 生成の規約準拠"""

def test_duplicate_handling():
    """重複ファイル名の処理"""

def test_dust_detection():
    """dust 判定の動作確認"""
```

### Integration Tests

```bash
# テスト用ファイルを @index/ に配置
cp tests/fixtures/*.md @index/

# 単一ファイル処理
python ollama_normalizer.py @index/test_engineer.md

# バッチ処理（プレビュー）
python ollama_normalizer.py --preview

# バッチ処理（実行）
python ollama_normalizer.py --all
```

### Acceptance Criteria Validation

| SC | 基準 | 検証方法 |
|----|-----|---------|
| SC-001 | 5 秒/ファイル以内 | 時間計測 |
| SC-002 | 分類精度 90%+ | 10 ファイルテスト |
| SC-003 | frontmatter 100% 準拠 | YAML バリデーション |
| SC-004 | @index 50%+ 削減/週 | 運用実績 |
| SC-005 | データ損失 0 件 | バックアップ比較 |

---

## Resume Capability（中断再開機能）

### 状態ファイル

**ファイル**: `@index/.processing_state.json`

```json
{
  "session_id": "2026-01-10T14:30:00",
  "started_at": "2026-01-10T14:30:00",
  "updated_at": "2026-01-10T14:35:00",
  "total_files": 50,
  "processed": [
    {
      "file": "AWS IAMの基礎.md",
      "status": "success",
      "destination": "エンジニア/AWS/AWS IAMの基礎.md",
      "timestamp": "2026-01-10T14:30:15"
    },
    {
      "file": "テスト.md",
      "status": "dust",
      "destination": "@dust/テスト.md",
      "timestamp": "2026-01-10T14:30:20"
    }
  ],
  "pending": ["未処理ファイル1.md", "未処理ファイル2.md"],
  "errors": []
}
```

### 再開ロジック

```
1. 起動時に .processing_state.json を確認
2. 存在する場合:
   - "前回の処理が中断されています。続行しますか？ (y/n/reset)"
   - y: pending から処理を再開
   - n: 終了
   - reset: 状態ファイルを削除して最初から
3. 存在しない場合:
   - 新規セッションとして開始
4. 各ファイル処理後に状態ファイルを更新
5. 全ファイル完了後に状態ファイルを削除
```

### コマンドオプション

```bash
# 通常実行（中断時は確認プロンプト）
python3 ollama_normalizer.py --all

# 強制的に最初から
python3 ollama_normalizer.py --all --reset

# 状態確認のみ
python3 ollama_normalizer.py --status
```

---

## Risk Mitigation

| リスク | 対策 |
|-------|------|
| Ollama 接続エラー | リトライ機構、タイムアウト設定 |
| 誤分類 | 確信度閾値 (0.7)、プレビューモード |
| 大量ファイル処理 | 確認プロンプト、バッチサイズ制限 |
| ファイル破損 | 移動前バックアップ、ロールバック機能 |
| **処理中断** | **状態ファイルによる再開機能** |

---

## Claude Code Integration

**コマンド定義** (`.claude/commands/og/`):

| コマンド | ファイル | 機能 |
|---------|---------|------|
| `/og:organize` | `og/organize.md` | 全ファイル一括整理 |
| `/og:preview` | `og/preview.md` | 処理内容プレビュー |
| `/og:single <file>` | `og/single.md` | 単一ファイル処理 |

**トリガーワード**:
- `整理して`, `indexの整理`, `index整理` → `/og:organize`
- `整理プレビュー`, `プレビュー` → `/og:preview`

**実行フロー**:
```
User: /og:organize
  ↓
Claude: コマンド読み込み → Bash 実行
  ↓
Bash: python3 .claude/scripts/ollama_normalizer.py --all
  ↓
Claude: 結果 JSON を整形表示
```

---

## Approval

- [ ] 実装計画承認
- [ ] Phase 1 完了
- [ ] Phase 2 完了
- [ ] Phase 3 完了
- [ ] 全体テスト完了
