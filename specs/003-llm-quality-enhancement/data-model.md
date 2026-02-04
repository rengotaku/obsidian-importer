# Data Model: ローカルLLM品質向上

**Date**: 2026-01-11
**Feature**: 003-llm-quality-enhancement

---

## Entities

### 1. SourceFile

処理対象のMarkdownファイル。

```python
class SourceFile(TypedDict):
    path: Path                  # ファイルパス
    name: str                   # ファイル名（拡張子なし）
    raw_content: str            # 元のファイル内容
    frontmatter: dict | None    # 既存のfrontmatter（あれば）
    body: str                   # frontmatter以降の本文
    language: str               # 検出された主言語 ("ja", "en", "mixed")
    is_complete_document: bool  # 完全な文書か断片的メモか
```

### 2. NormalizationResult

LLMによる正規化結果。

```python
class NormalizationResult(TypedDict):
    # ジャンル分類
    genre: Literal["エンジニア", "ビジネス", "経済", "日常", "その他", "dust"]
    confidence: float           # 0.0-1.0

    # 生成メタデータ
    frontmatter: Frontmatter

    # コンテンツ
    normalized_content: str     # LLMが改善した本文

    # 判定詳細
    is_dust: bool
    dust_reason: str | None
    related_keywords: list[str]  # 関連ファイル検索用

    # 品質情報
    improvements_made: list[str]  # 行った改善のリスト
```

### 3. Frontmatter

Obsidian規約に準拠したfrontmatter。

```python
class Frontmatter(TypedDict):
    title: str                  # ファイル名として使用
    tags: list[str]             # 3-5個のタグ
    created: str                # YYYY-MM-DD形式
    normalized: Literal[True]   # 常にTrue

    # @review用の追加フィールド（低確信度時のみ）
    review_confidence: float | None
    review_reason: str | None
```

### 4. TagDictionary

既存ナレッジベースから抽出したタグ語彙。

```python
class TagDictionary(TypedDict):
    # カテゴリ別タグリスト
    languages: list[str]        # プログラミング言語
    infrastructure: list[str]   # インフラ・DevOps
    tools: list[str]            # ツール・ソフトウェア
    concepts: list[str]         # 概念・分野
    lifestyle: list[str]        # 日常・趣味

    # メタ情報
    total_count: int
    extracted_at: str           # ISO形式タイムスタンプ
    source_vaults: list[str]    # 抽出元Vault
```

### 5. ProcessingSession

バッチ処理のセッション管理。

```python
class ProcessingSession(TypedDict):
    session_id: str             # タイムスタンプベース
    started_at: str
    updated_at: str

    # ファイル管理
    total_files: int
    pending: list[str]          # 未処理ファイル名
    processed: list[ProcessedFile]
    errors: list[ErrorRecord]

    # 統計
    stats: ProcessingStats
```

### 6. ProcessingStats

処理統計。

```python
class ProcessingStats(TypedDict):
    success: int                # 正常処理
    dust: int                   # dust判定
    review: int                 # @review送り
    skipped: int                # スキップ（確信度低）
    error: int                  # エラー
```

---

## Relationships

```
SourceFile
    │
    ▼ (Ollama API)
NormalizationResult
    │
    ├── Frontmatter
    │       │
    │       ▼ (参照)
    │   TagDictionary
    │
    ▼ (後処理)
ProcessedFile
    │
    ├── → Vault (confidence >= 0.7)
    ├── → @review (confidence < 0.7)
    └── → @dust (is_dust = true)
```

---

## State Transitions

### File Processing States

```
[未処理] ─────────────────────────────────────────────────┐
    │                                                     │
    ▼ (読み込み)                                          │
[分析中] ───────────────────────────────────────────┐     │
    │                                               │     │
    ├── confidence >= 0.7 ──▶ [正規化済み] ──▶ Vault │     │
    │                                               │     │
    ├── confidence < 0.7 ───▶ [要確認] ──▶ @review  │     │
    │                                               │     │
    ├── is_dust = true ─────▶ [廃棄] ──▶ @dust      │     │
    │                                               │     │
    └── エラー ─────────────▶ [エラー] ──▶ ログ記録 ─┘     │
                                                          │
[スキップ] ◀────────── 読み込みエラー ────────────────────┘
```

---

## Validation Rules

### Frontmatter

| フィールド | ルール |
|-----------|--------|
| title | 必須、1-200文字、ファイルシステム禁止文字なし |
| tags | 必須、3-5個、各タグ1-50文字 |
| created | 必須、YYYY-MM-DD形式 |
| normalized | 必須、常にtrue |

### NormalizationResult

| フィールド | ルール |
|-----------|--------|
| genre | GENRES定数のいずれか |
| confidence | 0.0-1.0の範囲 |
| normalized_content | 空でない文字列 |
| is_dust & genre | is_dust=true ⇔ genre="dust" |

### TagDictionary

| ルール |
|--------|
| 各カテゴリ最大30タグ |
| タグは小文字・ハイフン形式に正規化 |
| 重複タグなし |

---

## Storage Format

### Session Files (@plan/{session_id}/)

```
@plan/
└── 20260111_143000/
    ├── session.json      # ProcessingSession メタデータ
    ├── pending.json      # 未処理ファイルリスト
    ├── processed.json    # 処理済みファイルリスト
    ├── errors.json       # エラー記録
    ├── results.json      # 処理結果サマリー
    └── execution.log     # 実行ログ
```

### Tag Dictionary (.claude/scripts/data/)

```
.claude/scripts/data/
└── tag_dictionary.json   # TagDictionary
```

---

## Migration Notes

既存の`ollama_normalizer.py`からの変更点:

1. **NormalizationResult拡張**: `improvements_made`フィールド追加
2. **Frontmatter拡張**: `review_confidence`, `review_reason`追加
3. **TagDictionary新規**: プロンプト注入用のタグ辞書
4. **@review対応**: 低確信度ファイルの新規振り分け先

既存のセッション管理（@plan/）は互換性を維持。
