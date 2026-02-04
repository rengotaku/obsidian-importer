# Research: Phase 2 簡素化

## 1. 既存コード構造の分析

### 1.1 KnowledgeDocument クラス (knowledge_extractor.py)

**現在のフィールド:**
```python
@dataclass
class KnowledgeDocument:
    title: str
    tags: list[str]              # ← 削除対象
    created: str
    source_provider: str
    source_conversation: str
    overview: str                # ← まとめ に改名
    key_learnings: list[str]
    action_items: list[str]      # ← 削除対象
    code_snippets: list[CodeSnippet]
    related_links: list[str]     # ← 削除対象
    normalized: bool
```

**変更点:**
- `tags` フィールドを削除
- `action_items` フィールドを削除
- `related_links` フィールドを削除
- `overview` を `summary_content` に改名（`## まとめ` 用）
- `summary` フィールドを追加（frontmatter 用、1行の要約）

### 1.2 to_markdown() メソッド

**現在の出力セクション:**
1. frontmatter (title, tags, created, source_provider, source_conversation, normalized)
2. `## 概要`
3. `## 主要な学び`
4. `## 実践的なアクション` ← 削除対象
5. `## コードスニペット`
6. `## 関連` ← 削除対象

**変更点:**
- frontmatter から `tags:` セクションを削除
- frontmatter に `summary:` を追加（1行の要約）
- `## 概要` → `## まとめ` に改名
- `## 実践的なアクション` セクションを削除
- `## 関連` セクションを削除

### 1.3 knowledge_extraction.txt プロンプト

**現在の出力フォーマット:**
```json
{
  "title": "...",           // ← 削除（会話タイトルを使用）
  "overview": "...",        // ← summary_content に改名
  "key_learnings": [...],
  "action_items": [...],    // ← 削除
  "code_snippets": [...],
  "tags": [...],            // ← 削除
  "related_keywords": [...]  // ← 削除
}
```

**変更後（2つのプロンプト）:**

**プロンプト A: Summary 翻訳用**（Summary がある場合のみ）
```json
{
  "summary": "日本語に翻訳された要約"
}
```

**プロンプト B: まとめ生成用**
```json
{
  "summary": "1行の要約",           // Summary なしの場合のみ
  "summary_content": "構造化されたまとめ（Markdown形式）",
  "key_learnings": [...],
  "code_snippets": [...]
}
```

**変更点:**
- プロンプトを2分割（翻訳用 / まとめ生成用）
- `title`, `tags`, `related_keywords`, `action_items` の抽出指示を削除
- 構造化指示を追加（会話内容に適した形式を使用、特定形式を強制しない）

### 1.4 _generate_filename() (cli.py)

**現在のロジック:**
```python
def _generate_filename(conv: BaseConversation) -> str:
    date_str = conv.created_at[:10] if conv.created_at else ""
    title = sanitize_filename(conv.title, max_length=60)
    if date_str:
        return f"{date_str}_{title}"  # ← 日付プレフィックス付き
    return title
```

**変更点:**
- 日付プレフィックスを削除
- 会話タイトルから日付プレフィックス（`YYYY-MM-DD_`）を除去

### 1.5 Phase 3 呼び出し (cli.py)

**現在のロジック:**
- `cmd_process()` 内で `--skip-normalize` フラグがない場合に `run_normalizer()` を呼び出し
- Phase 3 は `/og:organize` の役割と重複

**変更点:**
- `--skip-normalize` 引数を削除
- Phase 3 呼び出しブロックを削除
- `run_normalizer()` 関数を削除

---

## 2. 設計決定

### 2.1 タイトル処理

**Decision**: 会話タイトルから日付プレフィックスを除去して使用

**Rationale**:
- LLM でタイトル生成すると元の会話との関連性が失われる可能性
- 会話タイトルは既に適切な名前が付いている
- 処理の単純化

**Alternatives considered**:
- LLM でタイトル生成（却下: 重複処理、品質不安定）

### 2.2 構造化されたまとめ

**Decision**: プロンプトで「会話内容に適した構造を使用」と指示。特定形式を強制しない。

**会話内容に応じた形式:**

| 会話の内容 | 適切な形式 |
|-----------|-----------|
| 比較・スペック | 表 |
| 手順・ステップ | 番号付きリスト |
| 複数トピック | 小見出し + 箇条書き |
| 単一トピック | 段落 + 箇条書き |

**プロンプト指示内容**:
- 会話内容に適した構造（表、リスト、見出し、段落）を使用
- 壁のテキスト（構造のない長文）は禁止
- 特定形式を強制しない

**Rationale**:
- 会話の性質によって最適な表現形式が異なる
- 読みやすさの向上

### 2.3 Summary の処理（2段階 LLM）

**Decision**: Summary 翻訳と まとめ生成を分離。別々の LLM 呼び出しで処理。

**処理フロー**:

```
Parse 出力
    │
    ├─ ## Summary あり
    │      │
    │      ├─ Step 1: Summary のみを LLM に渡して翻訳
    │      │          → frontmatter.summary
    │      │
    │      └─ Step 2: Summary を除去した会話内容を LLM に渡す
    │                 → まとめ, 学び, コードスニペット
    │
    └─ ## Summary なし
           │
           └─ Step 1 のみ: 会話内容を LLM に渡す
                          → summary, まとめ, 学び, コードスニペット
```

**Rationale**:
- Summary 翻訳は単純なタスク、会話内容の構造化は複雑なタスク
- 分離することで各タスクの品質が向上
- Summary がある場合、会話内容に Summary を含めると重複情報になる

### 2.4 テスト方針

**Decision**: 既存テストを修正し、新仕様に合わせる

**修正点**:
- `MOCK_LLM_RESPONSE` から `title`, `tags`, `related_keywords`, `action_items` を削除
- `to_markdown()` テストから `tags`, `## 実践的なアクション`, `## 関連` の検証を削除
- `## 概要` → `## まとめ` に変更
- 新しい `summary` フィールドのテストを追加

---

## 3. 影響範囲

### 3.1 修正ファイル一覧

| ファイル | 修正内容 |
|---------|---------|
| `scripts/llm_import/prompts/summary_translation.txt` | 新規: Summary 翻訳用プロンプト |
| `scripts/llm_import/prompts/knowledge_extraction.txt` | まとめ生成用に簡素化 |
| `scripts/llm_import/common/knowledge_extractor.py` | 2段階LLM処理、KnowledgeDocument修正 |
| `scripts/llm_import/cli.py` | _generate_filename(), Phase 3 削除 |
| `scripts/llm_import/tests/test_knowledge_extractor.py` | テスト更新 |
| `.claude/commands/og/import-claude.md` | ドキュメント更新（済） |

### 3.2 下流への影響

- **`/og:organize`**: 入力形式が変わるが、frontmatter を読み取って処理するため影響なし
- **既存出力ファイル**: 19件の既存出力は再処理または手動修正が必要

### 3.3 後方互換性

- 新しい出力形式は `/og:organize` で問題なく処理可能（`tags` がなくても付与）
- 既存の19件は `normalized: false` のため、再処理可能
