# Research: Summary 日本語化

**Feature**: 008-japanese-summary
**Date**: 2026-01-13

## 調査 1: Summary セクションのパターン

### 調査対象

Claude エクスポート由来ファイルの Summary 記述形式を確認。

### 発見

ファイル例: `エンジニア/60A回路で冬の暖房とサーバーがトリップする原因と対策.md`

```markdown
## Winter heating overload on 60A circuit

## Summary

**Conversation Overview**

The user contacted Claude about electrical circuit breaker issues...
```

### パターン

| パターン | 出現 | 例 |
|---------|------|-----|
| `## Summary` | 高頻度 | Claude エクスポートの標準形式 |
| `**Conversation Overview**` | 高頻度 | Summary 内の小見出し |
| `## [English Title]` | 中頻度 | 英語タイトルの見出し |

### Decision

以下のパターンを翻訳対象とする:
- `## Summary` → `## 概要`
- `**Conversation Overview**` → `**会話の概要**`
- Summary セクション内の英語本文 → 日本語に翻訳

## 調査 2: 既存の英語処理

### 現状

`stage3_normalize.txt` の現在のルール:
```
3. **断片的な英語メモ** → 自然な日本語に（英語文書でない場合）
...
## 保持すべき点
- 完全な英語文書は翻訳しない
```

`is_english_doc` フラグ:
- 文書全体が英語かどうかを判定
- `True` の場合、Stage 3 で翻訳をスキップ

### 問題点

- Summary セクションは「完全な英語文書」ではなく「英語で書かれた部分」
- 現在のルールでは Summary が翻訳されない

### Decision

プロンプトに **例外ルール** を追加:
- Summary/Conversation Overview は「完全な英語文書」ルールの例外
- 常に日本語に翻訳する

## 実装方針

### 変更箇所

ファイル: `.claude/scripts/prompts/stage3_normalize.txt`

### 変更内容

「改善すべき点」セクションに項目 4 を追加:

```
4. **英語の Summary/Conversation Overview** → 日本語に翻訳
   - 「## Summary」→「## 概要」
   - 「**Conversation Overview**」→「**会話の概要**」
   - Summary 内の英文は全て日本語に翻訳
   - この翻訳は「完全な英語文書は翻訳しない」ルールより優先
```

### 理由

- Stage 3 は既にコンテンツ正規化を担当
- 新規 Stage 追加は LLM 呼び出し増加につながる
- プロンプト拡張で対応可能

## Alternatives Considered

| 選択肢 | 評価 | 却下理由 |
|--------|------|---------|
| 新規 Stage 3.5 追加 | ❌ | LLM 呼び出し増加、処理時間増 |
| Python で事前置換 | ❌ | パターンマッチだけでは意味保持が困難 |
| Stage 3 プロンプト拡張 | ✅ | 最小限の変更で対応可能 |
