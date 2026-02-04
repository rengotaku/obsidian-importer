# Research: LLM レスポンス形式をマークダウンに変更

**Date**: 2026-01-30
**Feature**: 042-llm-markdown-response

## Decision 1: マークダウンレスポンスの構造設計

### Decision

LLM に以下のマークダウン構造で応答させる:

```markdown
# タイトル

## 要約

1-2文の要約テキスト

## 内容

構造化されたまとめ（現在の summary_content と同等）
```

### Rationale

- `#` 見出しでタイトルを明示 → パースが容易
- `## 要約` セクションで summary を分離 → 見出しレベルで区別
- `## 内容` セクションが本体 → 現在の `summary_content` に対応
- 現行の JSON 形式の 3 フィールド（title, summary, summary_content）と 1:1 対応を維持
- タグセクションは含めない（現行パイプラインにタグフィールドが存在しないため、後方互換性を優先）

### Alternatives Considered

1. **YAML frontmatter + Markdown body**: `---` で区切った YAML ヘッダー + 本文
   - 却下理由: LLM が YAML の厳密なインデントを守れない可能性、JSON と同様の構造的制約
2. **セクション区切りなし（自由形式）**: LLM に自由に書かせてヒューリスティクスで抽出
   - 却下理由: パースの信頼性が低い、フィールド欠落が多発する可能性

## Decision 2: マークダウンパーサーの実装方針

### Decision

正規表現ベースのセクションパーサーを新規作成する。外部ライブラリは使用しない。

### Rationale

- 対象となるマークダウンは LLM プロンプトで構造を指示した限定的なフォーマット
- 必要な処理: 見出しの検出、セクション分割、リスト項目の抽出のみ
- Python 標準ライブラリの `re` モジュールで十分
- プロジェクトの方針（標準ライブラリ中心）に合致

### Alternatives Considered

1. **markdown-it-py / mistune**: 外部 Markdown パーサー
   - 却下理由: 外部依存の追加は最小限にする方針。AST 生成は過剰
2. **LLM に JSON + Markdown のハイブリッド形式で応答させる**: メタデータは JSON、本文は Markdown
   - 却下理由: 結局 JSON パースが残り、品質向上の動機を損なう

## Decision 3: プロンプト変更の範囲

### Decision

2 つのプロンプトテンプレートを変更する:

1. **knowledge_extraction.txt**: JSON 出力指示 → マークダウン出力指示に全面変更
2. **summary_translation.txt**: JSON 出力指示 → マークダウン出力指示に変更

### Rationale

- knowledge_extraction.txt は本機能の中核
- summary_translation.txt も JSON 応答を求めているため、一貫性のために同時変更
- 両方のパースロジックを統一できる

### Alternatives Considered

1. **knowledge_extraction.txt のみ変更**: summary_translation.txt は JSON のまま
   - 却下理由: 2 種類のパースロジックを維持する複雑さ。一貫性を優先

## Decision 4: 後方互換性の維持方法

### Decision

マークダウンパーサーの出力を、現在の `parse_json_response()` が返すのと同じ `dict` 形式に変換する。呼び出し元（`KnowledgeExtractor`）の変更を最小限にする。

### Rationale

- `parse_json_response()` → `parse_markdown_response()` に置き換え
- 戻り値の型 `tuple[dict, str | None]` は維持
- `dict` のキー（`title`, `summary`, `summary_content`）も維持
- `KnowledgeExtractor` 側の変更は関数呼び出し先の変更のみ

### Alternatives Considered

1. **`ExtractionResult` を直接返す新 API**: パーサーが直接 `KnowledgeDocument` を構築
   - 却下理由: 変更範囲が大きい。段階的リファクタリングが安全

## Decision 5: コードブロックフェンス除去の処理

### Decision

パース前の前処理として、レスポンス全体が ````markdown ... ```` で囲まれている場合にフェンスを除去する。

### Rationale

- LLM は指示されなくてもコードブロックで囲むことがある
- 現在の JSON パーサーにも同様の処理がある（`extract_json_from_code_block`）
- マークダウンパーサーの前処理として自然な位置

## Decision 6: summary_translation のマークダウン形式

### Decision

翻訳プロンプトのレスポンスは以下の最小マークダウン構造とする:

```markdown
## 要約

翻訳された日本語のサマリー（1-2文）
```

### Rationale

- 翻訳は 1 フィールドのみ（summary）なので最小構造で十分
- `## 要約` 見出しの後のテキストを抽出するだけ
- knowledge_extraction と同じパースパターンを再利用可能
