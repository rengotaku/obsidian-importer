# Implementation Plan: 出力ファイル品質改善

**Branch**: `049-output-quality-improve` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/049-output-quality-improve/spec.md`

## Summary

LLM 出力の品質問題（空コンテンツ、絵文字タイトル、プレースホルダー、トピック粒度、summary 長さ）を修正する。transform/nodes.py と organize/nodes.py のバリデーション/サニタイズ機能を強化し、プロンプト改善を行う。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, requests (Ollama API)
**Storage**: ファイルシステム（JSON, JSONL, Markdown）、Kedro DataCatalog
**Testing**: unittest（標準ライブラリ）
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single (Kedro パイプライン)
**Performance Goals**: パイプライン処理時間が現行比 110% 以内
**Constraints**: Ollama LLM ローカル稼働、既存テスト 100% 通過
**Scale/Scope**: 数百〜数千の会話ファイルを処理

## Constitution Check

*GATE: Constitution file が存在しないため、既存プロジェクトの慣例に従う*

- ✅ 単一プロジェクト構造を維持
- ✅ 既存の Kedro パイプラインパターンに従う
- ✅ unittest を使用（pytest 不使用）
- ✅ レガシーコード (`src/converter/`) は修正しない

## Project Structure

### Documentation (this feature)

```text
specs/049-output-quality-improve/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── pipelines/
│   ├── transform/
│   │   ├── __init__.py
│   │   ├── nodes.py        # FR-001〜FR-006, FR-009 修正対象
│   │   └── pipeline.py
│   └── organize/
│       ├── __init__.py
│       ├── nodes.py        # FR-008 修正対象
│       └── pipeline.py
└── utils/
    └── prompts/
        └── knowledge_extraction.txt  # FR-007 修正対象

tests/
├── pipelines/
│   ├── transform/
│   │   └── test_nodes.py   # ユニットテスト追加
│   └── organize/
│       └── test_nodes.py   # ユニットテスト追加
└── e2e/
    └── test_golden_comparator.py  # E2E テスト
```

**Structure Decision**: 既存の Kedro パイプライン構造を維持。新規ファイルは作成せず、既存ファイルの修正のみ。

## Complexity Tracking

> 違反なし - 既存構造を維持し、シンプルな修正のみ

## Phase 0: Research

### R-001: 絵文字除去の正規表現パターン

**Task**: Unicode Emoji カテゴリを網羅する正規表現パターンの調査

**Decision**: Python の `re` モジュール + Unicode カテゴリマッチング

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

**Alternatives considered**:
- `emoji` ライブラリ: 依存追加が必要、標準ライブラリで対応可能
- unicodedata.category: 文字単位の判定で効率が悪い

### R-002: 空コンテンツ判定基準

**Task**: `summary_content` が「空」と判定される条件の定義

**Decision**: 空白文字のみの場合も空として扱う

```python
def is_empty_content(content: str | None) -> bool:
    """Return True if content is empty or whitespace-only."""
    if content is None:
        return True
    return not content.strip()
```

**Rationale**: 空白のみのコンテンツは実質的に価値がなく、出力する意味がない

### R-003: プレースホルダー検出パターン

**Task**: LLM が採用すべきでないプレースホルダーパターンの特定

**Decision**: 正規表現でプレースホルダーパターンを検出

検出対象:
- `(省略)`, `（省略）`
- `[トピック名]`, `[タイトル]`, `[例]`
- `<...>`, `...`

**Rationale**: これらはプロンプト例文に由来する典型的なプレースホルダー

### R-004: トピック抽象度のプロンプト指示

**Task**: 適切な抽象度でトピックを抽出するためのプロンプト改善

**Decision**: プロンプトに明示的な抽象度指示を追加

```text
主題を抽出する際は、具体的な商品名・料理名・固有名詞ではなく、
カテゴリレベルで答えてください。

例:
- NG: バナナプリン → OK: 離乳食
- NG: iPhone 15 Pro → OK: スマートフォン
- NG: Claude 3.5 Sonnet → OK: AI
```

**Rationale**: LLM に期待する抽象度を具体例で示すことで、一貫した出力を得る

## Phase 1: Design

### Data Model

#### ValidationResult

```python
@dataclass
class ValidationResult:
    """Result of content validation."""
    passed: bool
    skip_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
```

**Usage**: `extract_knowledge` ノードで `summary_content` の検証結果を表現

#### 既存エンティティの拡張

`ProcessedItem` (dict) に以下のフィールドを追加検証:
- `generated_metadata.summary_content`: 空チェック (FR-001)
- `generated_metadata.title`: サニタイズ処理 (FR-003〜FR-006)
- `generated_metadata.summary`: 長さ警告 (FR-009)

### API Contracts

本 feature は CLI パイプラインのため、REST API は該当なし。

### Node Modifications

#### 1. `extract_knowledge` (transform/nodes.py)

**追加処理**:
- summary_content 空チェック → スキップ + ログ記録 (FR-001, FR-002)
- summary 長さ警告 (FR-009)

```python
# Line ~113-116 の後に追加
summary_content = knowledge.get("summary_content", "")
if not summary_content or not summary_content.strip():
    logger.warning(f"Empty summary_content for {partition_id}. Item excluded.")
    skipped_empty += 1
    continue

# summary 長さ警告
summary = knowledge.get("summary", "")
if len(summary) > 500:
    logger.warning(f"Long summary ({len(summary)} chars) for {partition_id}")
```

#### 2. `_sanitize_filename` (transform/nodes.py)

**拡張**:
- 絵文字除去 (FR-003)
- ブラケット除去 `[]()` (FR-004)
- ファイルパス記号除去 `~%` (FR-005)
- 空タイトルフォールバック (FR-006)

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

#### 3. `knowledge_extraction.txt` (prompts)

**追加ルール** (FR-007):
- プレースホルダー禁止ルールを明記

```text
## 禁止事項

タイトルに以下を含めないでください:
- プレースホルダー: `(省略)`, `（省略）`, `[トピック名]`, `[タイトル]`
- 省略記号のみ: `...`, `<...>`
- 例文からの引用

タイトルは会話の実際の内容を反映する具体的なものにしてください。
```

#### 4. `_extract_topic_via_llm` (organize/nodes.py)

**プロンプト改善** (FR-008):
- 抽象度指示を追加

```python
prompt = f"""この会話から主題（トピック）を1つ抽出してください。

会話内容:
{body[:1000]}

主題をカテゴリレベル（1-3単語）で答えてください。
具体的な商品名・料理名・固有名詞ではなく、上位概念で答えてください。

例:
- バナナプリンの作り方 → 離乳食
- iPhone 15 Pro の設定 → スマートフォン
- Claude 3.5 Sonnet の使い方 → AI

抽出できない場合は空文字を返してください。"""
```

## Implementation Phases

### Phase 1: Setup & Validation

1. 現状の E2E テスト (`make test-e2e`) が PASS することを確認
2. テストフィクスチャに問題ケース（空コンテンツ、絵文字タイトル等）を追加

### Phase 2: Core Implementation (TDD)

**US1 (空コンテンツ除外)**:
1. `extract_knowledge` に空チェック追加
2. スキップカウンターとログ記録
3. ユニットテスト作成

**US2 (タイトルサニタイズ)**:
1. EMOJI_PATTERN 定義追加
2. `_sanitize_filename` 拡張
3. ユニットテスト作成

**US5 (summary 長さ)**:
1. 500 文字超で警告ログ出力
2. ユニットテスト作成

### Phase 3: Prompt Improvements

**US3 (プレースホルダー防止)**:
1. `knowledge_extraction.txt` に禁止ルール追加
2. E2E テストで検証

**US4 (トピック粒度)**:
1. `_extract_topic_via_llm` プロンプト改善
2. E2E テストで検証

### Phase 4: Integration & Polish

1. 全テスト実行 (`make test`)
2. E2E テスト実行 (`make test-e2e`)
3. ゴールデンファイル更新 (`make test-e2e-update-golden`)
4. コードレビュー

## Risk Mitigation

| リスク | 軽減策 |
|--------|--------|
| 絵文字パターン不完全 | Unicode 15.1 の主要カテゴリをカバー、問題発生時に追加 |
| プロンプト変更で品質低下 | E2E テストでゴールデンファイル比較 |
| 既存テスト破壊 | 各変更後に `make test` 実行 |
| パフォーマンス劣化 | 正規表現はコンパイル済みパターンを使用 |

## Success Metrics

- [ ] SC-001: 出力ファイルの 100% が空でない本文を持つ
- [ ] SC-002: 出力ファイル名の 100% が絵文字・問題シンボルを含まない
- [ ] SC-003: プレースホルダータイトルの発生率 0%
- [ ] SC-004: トピック抽象度が適切なファイル 90% 以上
- [ ] SC-005: summary が 500 文字超のケース 5% 未満
- [ ] SC-006: 既存ユニットテスト 100% 通過
- [ ] SC-007: パイプライン処理時間 現行比 110% 以内
