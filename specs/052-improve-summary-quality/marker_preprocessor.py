#!/usr/bin/env python3
"""
マーカー前処理・後処理モジュール

コードブロックと表形式データを抽出し、マーカーに置換。
LLM処理後にマーカーを元のコンテンツに復元する。
"""

import re
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    """抽出されたコンテンツ"""

    content_type: str  # "code" or "table"
    marker: str  # "**code-1**" or "**table-1**"
    original: str  # 元のコンテンツ
    header: str  # 分類用（コード言語 or 表ヘッダー）
    position: int  # 元の位置（最新判定用）


def extract_code_blocks(text: str) -> list[tuple[str, str, int]]:
    """コードブロックを抽出: (full_match, language, position)"""
    pattern = r"```(\w*)\n(.*?)```"
    matches = []
    for m in re.finditer(pattern, text, re.DOTALL):
        lang = m.group(1) or "unknown"
        matches.append((m.group(0), lang, m.start()))
    return matches


def extract_tables(text: str) -> list[tuple[str, str, int]]:
    """Markdown表を抽出: (full_match, header, position)"""
    # 表パターン: |で始まる行が連続
    pattern = r"(\|[^\n]+\|\n(?:\|[-:| ]+\|\n)?(?:\|[^\n]+\|\n?)+)"
    matches = []
    for m in re.finditer(pattern, text):
        table = m.group(0)
        # ヘッダー行を取得（最初の行）
        header_line = table.split("\n")[0].strip()
        matches.append((table, header_line, m.start()))
    return matches


@dataclass
class TableWithHeading:
    """見出し付きの表"""

    heading: str  # 直前の見出し (## ...)
    table: str  # 表本体
    columns: str  # カラム名（最新判定用）
    position: int  # 元の位置


def extract_tables_with_headings(text: str) -> list[TableWithHeading]:
    """表と直前の見出しをセットで抽出"""
    results = []

    # 見出しパターン: ## または ### で始まる行
    heading_pattern = r"^(#{2,3}\s+.+)$"
    # 表パターン
    table_pattern = r"(\|[^\n]+\|\n(?:\|[-:| ]+\|\n)?(?:\|[^\n]+\|\n?)+)"

    lines = text.split("\n")
    current_heading = ""

    for m in re.finditer(table_pattern, text, re.MULTILINE):
        table = m.group(0)
        pos = m.start()

        # 表の直前のテキストから見出しを探す
        text_before = text[:pos]
        heading_matches = list(re.finditer(heading_pattern, text_before, re.MULTILINE))
        if heading_matches:
            current_heading = heading_matches[-1].group(1)
        else:
            current_heading = ""

        # カラム名（最初の行）
        columns = table.split("\n")[0].strip()

        results.append(
            TableWithHeading(
                heading=current_heading,
                table=table,
                columns=columns,
                position=pos,
            )
        )

    return results


def select_latest_tables(tables: list[TableWithHeading]) -> list[TableWithHeading]:
    """同じカラム名の表は最新のみ保持、異なるカラムは全て保持"""
    by_columns: dict[str, TableWithHeading] = {}
    for t in tables:
        # 同じカラム名なら上書き（最新が残る）
        by_columns[t.columns] = t
    return list(by_columns.values())


def select_latest_by_header(items: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    """同じヘッダーのものは最新（最後）のみを選択"""
    by_header: dict[str, tuple[str, str, int]] = {}
    for content, header, pos in items:
        by_header[header] = (content, header, pos)
    return list(by_header.values())


@dataclass
class PreprocessResult:
    """前処理結果"""

    processed_text: str  # LLM に渡すテキスト
    code_markers: dict[str, str]  # コードマーカー → 元コード
    extracted_tables: list[TableWithHeading]  # 抽出した表（見出し付き）


def preprocess(text: str) -> PreprocessResult:
    """
    テキストを前処理

    - コード: マーカーに置換して LLM に渡す
    - 表: 抽出して LLM には渡さない（後で追加）
    """
    code_markers: dict[str, str] = {}
    processed = text

    # コードブロック処理: マーカーに置換
    code_blocks = extract_code_blocks(text)

    for i, (content, lang, pos) in enumerate(code_blocks, 1):
        marker = f"**code-{i}**"
        code_markers[marker] = content
        processed = processed.replace(content, marker, 1)

    # 表処理: 抽出して削除（LLM には渡さない）
    tables_with_headings = extract_tables_with_headings(processed)
    selected_tables = select_latest_tables(tables_with_headings)

    # 表をテキストから削除
    for t in tables_with_headings:
        processed = processed.replace(t.table, "", 1)

    return PreprocessResult(
        processed_text=processed,
        code_markers=code_markers,
        extracted_tables=selected_tables,
    )


@dataclass
class PostprocessResult:
    """後処理結果"""

    output: str  # 最終出力
    needs_review: bool  # review 行きフラグ
    review_reason: str | None  # review 理由
    fallback_used: bool  # フォールバック使用フラグ
    markers_found: list[str]  # 見つかったマーカー
    markers_missing: list[str]  # 欠落したマーカー


def postprocess(text: str, preprocess_result: PreprocessResult) -> PostprocessResult:
    """
    後処理: コードマーカー復元 + 表追加

    - コードマーカーが存在 → 置換
    - コードマーカー一部欠落 → 末尾に追加
    - コードマーカー全欠落 → review 行き
    - 表 → 常に末尾に追加（見出し付き）
    """
    code_markers = preprocess_result.code_markers
    tables = preprocess_result.extracted_tables

    result = text
    markers_found = []
    markers_missing = []

    # コードマーカー処理
    if code_markers:
        for marker, original in code_markers.items():
            if marker in result:
                result = result.replace(marker, original)
                markers_found.append(marker)
            else:
                markers_missing.append(marker)

        # コードマーカー全欠落 → review 行き
        if len(markers_found) == 0 and len(markers_missing) > 0:
            # 表は追加してから review 行き
            if tables:
                result += _format_tables_section(tables)
            return PostprocessResult(
                output=result,
                needs_review=True,
                review_reason=f"コードマーカーが全て欠落: {markers_missing}",
                fallback_used=False,
                markers_found=markers_found,
                markers_missing=markers_missing,
            )

        # コードマーカー一部欠落 → フォールバック
        if markers_missing:
            fallback_section = "\n\n---\n\n## 補足コード\n\n"
            for marker in markers_missing:
                original = code_markers[marker]
                fallback_section += f"{original}\n\n"
            result += fallback_section

    # 表を末尾に追加（見出し付き）
    if tables:
        result += _format_tables_section(tables)

    return PostprocessResult(
        output=result,
        needs_review=False,
        review_reason=None,
        fallback_used=len(markers_missing) > 0,
        markers_found=markers_found,
        markers_missing=markers_missing,
    )


def _format_tables_section(tables: list[TableWithHeading]) -> str:
    """表セクションをフォーマット"""
    section = "\n\n---\n\n## データ\n\n"
    for t in tables:
        if t.heading:
            # 見出しレベルを ### に統一
            heading = t.heading.lstrip("#").strip()
            section += f"### {heading}\n\n"
        section += f"{t.table}\n"
    return section


def get_marker_prompt_instruction() -> str:
    """LLMに渡すコードマーカー保持指示"""
    return """
## ⚠️ 重要: コードマーカーの扱い

入力テキストに `**code-N**` というマーカーがある場合、
**必ず出力にそのまま含めてください**。

**絶対守るルール**:
1. マーカーは**削除禁止** - 必ず出力に含める
2. マーカーは**そのまま** - `**code-1**` を `**code-1**` として出力
3. マーカーの前に**簡潔な説明**を追加

**出力例**:
```
### データベース接続
PostgreSQLへの接続処理。環境変数から設定を読み込む。

**code-1**
```

**禁止事項**:
- マーカーを削除すること
- マーカーの内容を展開すること
- マーカーを別の形式に変えること
"""


if __name__ == "__main__":
    # S3 のテスト
    from pathlib import Path

    base = Path(__file__).parent / "verification-outputs"
    s3_text = (base / "S3-8b8869107b00/original.md").read_text()

    processed, markers = preprocess(s3_text)

    print("=== 抽出されたマーカー ===")
    for marker, content in markers.items():
        print(f"\n{marker}:")
        print(content[:200] + "..." if len(content) > 200 else content)

    print("\n=== 統計 ===")
    print(f"元サイズ: {len(s3_text)} chars")
    print(f"処理後: {len(processed)} chars")
    print(f"削減: {(1 - len(processed) / len(s3_text)) * 100:.1f}%")
    print(f"マーカー数: {len(markers)}")
