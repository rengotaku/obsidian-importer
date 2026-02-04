# Quickstart: Robust JSON Parsing

**Feature**: 005-robust-json-parse
**Date**: 2026-01-12

## 概要

`ollama_normalizer.py` の `parse_json_response` 関数を堅牢なJSON抽出ロジックに置き換える。

## 変更対象

- **ファイル**: `.claude/scripts/ollama_normalizer.py`
- **関数**: `parse_json_response` (行 881-897)

## 実装手順

### 1. 新しい関数を実装

```python
import re

# コードブロック抽出用正規表現
CODE_BLOCK_PATTERN = re.compile(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```')


def extract_json_from_code_block(response: str) -> str | None:
    """Markdownコードブロックからjsonを抽出"""
    match = CODE_BLOCK_PATTERN.search(response)
    return match.group(1) if match else None


def extract_first_json_object(text: str) -> str | None:
    """括弧バランス追跡で最初の完全なJSONオブジェクトを抽出"""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if char == '\\' and in_string:
            escape = True
            continue
        if char == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None


def parse_json_response(response: str) -> tuple[dict, str | None]:
    """Ollama応答からJSONを抽出・パース（堅牢版）"""
    if not response or not response.strip():
        return {}, "空の応答です"

    # 1. コードブロックを優先的に抽出
    json_str = extract_json_from_code_block(response)

    # 2. コードブロックがなければ括弧バランス追跡
    if not json_str:
        json_str = extract_first_json_object(response)

    if not json_str:
        return {}, "JSON形式の応答がありません"

    # 3. JSONパース
    try:
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        # エラー位置とコンテキストを含むメッセージ
        pos = e.pos
        context = json_str[max(0, pos-30):pos+30]
        return {}, f"JSONパースエラー: {e.msg} (位置 {pos})\nコンテキスト: ...{context}..."
```

### 2. テスト実行

```bash
# 単体テスト
python3 -c "
from ollama_normalizer import parse_json_response

# テストケース
tests = [
    ('{\"genre\": \"エンジニア\"}', True),
    ('結果: {\"genre\": \"ビジネス\"} 以上', True),
    ('\`\`\`json\n{\"genre\": \"経済\"}\n\`\`\`', True),
    ('JSONなし', False),
]

for input_str, should_succeed in tests:
    result, err = parse_json_response(input_str)
    success = err is None
    status = '✅' if success == should_succeed else '❌'
    print(f'{status} {input_str[:30]}... → {\"OK\" if success else err}')
"

# fixtureテスト
python3 ollama_normalizer.py tests/fixtures/tech_document.md --preview --diff
```

## 成功基準

- [ ] tech_document.md が正常に処理される
- [ ] 既存のテストケースが引き続き成功する
- [ ] 処理時間が10ms未満

## ロールバック

問題発生時は元の実装に戻す:

```bash
git checkout HEAD~1 -- .claude/scripts/ollama_normalizer.py
```
