# Research: 出力ファイル品質改善

**Branch**: `049-output-quality-improve` | **Date**: 2026-02-08

## R-001: 絵文字除去の正規表現パターン

### Decision

Python の `re` モジュール + Unicode カテゴリマッチングを使用。

```python
import re

# Emoji ranges from Unicode 15.1
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Flags
    "\U00002702-\U000027B0"  # Dingbats
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002600-\U000026FF"  # Misc symbols
    "]+",
    flags=re.UNICODE
)
```

### Rationale

- **標準ライブラリのみ**: 外部依存なしで実装可能
- **コンパイル済みパターン**: 実行時オーバーヘッド最小化
- **Unicode 15.1 カバレッジ**: 主要な絵文字カテゴリを網羅

### Alternatives Considered

| 方式 | メリット | デメリット | 採用 |
|------|----------|------------|------|
| `emoji` ライブラリ | 完全なカバレッジ | 依存追加が必要 | ❌ |
| `unicodedata.category` | 正確な分類 | 文字単位で非効率 | ❌ |
| 正規表現 + Unicode 範囲 | 標準ライブラリ、高速 | 一部漏れの可能性 | ✅ |

---

## R-002: 空コンテンツ判定基準

### Decision

空文字列または空白文字のみを「空」と判定。

```python
def is_empty_content(content: str | None) -> bool:
    """Return True if content is empty or whitespace-only."""
    if content is None:
        return True
    return not content.strip()
```

### Rationale

- **空白のみも除外**: 実質的に価値のないコンテンツを排除
- **None 安全**: LLM がフィールドを返さなかった場合に対応
- **シンプル**: 追加の依存なし

### Edge Cases

| ケース | 結果 | 理由 |
|--------|------|------|
| `None` | 空 | フィールド欠損 |
| `""` | 空 | 空文字列 |
| `"   "` | 空 | 空白のみ |
| `"\n\t"` | 空 | 制御文字のみ |
| `" a "` | 非空 | 実質コンテンツあり |

---

## R-003: プレースホルダー検出パターン

### Decision

プロンプトにプレースホルダー禁止ルールを追加。コード側での検出は行わない。

**禁止対象**:
- `(省略)`, `（省略）`
- `[トピック名]`, `[タイトル]`, `[例]`
- `...`, `<...>`

### Rationale

- **根本対策**: LLM に生成させない方が、後処理で除去するより効果的
- **プロンプト改善**: 禁止事項を明示することで LLM の出力品質向上
- **サニタイズとの組み合わせ**: ブラケット除去で二重の安全策

### Implementation

プロンプトに以下を追加:

```text
## 禁止事項

タイトルに以下を含めないでください:
- プレースホルダー: `(省略)`, `（省略）`, `[トピック名]`, `[タイトル]`
- 省略記号のみ: `...`, `<...>`
- 例文からの引用

タイトルは会話の実際の内容を反映する具体的なものにしてください。
```

---

## R-004: トピック抽象度のプロンプト指示

### Decision

「抽象度指示型」アプローチを採用。プロンプトに具体例付きで抽象度を指示。

### Rationale

| アプローチ | メリット | デメリット | 採用 |
|-----------|----------|------------|------|
| タグ参照型 | 既存タグと一貫性 | 実装複雑、タグ依存 | ❌ |
| 抽象度指示型 | シンプル、独立 | LLM 解釈に依存 | ✅ |
| ルールベース | 確実 | パターン管理困難 | ❌ |

### Implementation

プロンプトに以下を追加:

```text
主題をカテゴリレベル（1-3単語）で答えてください。
具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。

例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI
```

---

## R-005: ファイル名サニタイズ拡張

### Decision

既存の `_sanitize_filename` を拡張し、以下の文字を追加除去:

| カテゴリ | 対象文字 | 理由 |
|----------|---------|------|
| ブラケット | `[]()` | Wiki リンクと混同 |
| ファイルパス | `~%` | パス展開・エンコード問題 |
| 絵文字 | Unicode Emoji | ファイルシステム互換性 |

### Implementation

```python
def _sanitize_filename(title: str, file_id: str) -> str:
    # 1. 絵文字除去
    sanitized = EMOJI_PATTERN.sub("", title)

    # 2. 問題文字除去（拡張）
    unsafe_chars = r'[/\\:*?"<>|\[\]()~%]'
    sanitized = re.sub(unsafe_chars, "", sanitized)

    # 3. 空白正規化
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # 4. フォールバック
    if not sanitized:
        return file_id[:12]

    return sanitized[:250]
```

---

## Summary

| 課題 | 調査結果 | 採用アプローチ |
|------|----------|---------------|
| 絵文字除去 | 正規表現 + Unicode 範囲 | 標準ライブラリのみ |
| 空コンテンツ | strip() で判定 | シンプル実装 |
| プレースホルダー | プロンプト禁止ルール | 根本対策 |
| トピック粒度 | 抽象度指示型 | プロンプト改善 |
| サニタイズ拡張 | ブラケット・パス記号追加 | 既存関数拡張 |
