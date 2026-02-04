# Research: Robust JSON Parsing

**Feature**: 005-robust-json-parse
**Date**: 2026-01-12

## Research Tasks

### 1. Current Implementation Analysis

**Question**: 現在の `parse_json_response` の問題点は何か？

**Findings**:
現在の実装（ollama_normalizer.py:881-897）:
```python
def parse_json_response(response: str) -> tuple[dict, str | None]:
    try:
        if "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str), None
        return {}, "JSON形式の応答がありません"
    except json.JSONDecodeError as e:
        return {}, f"JSONパースエラー: {e}"
```

**問題点**:
1. `rfind("}")` で最後の `}` を取得 → 複数JSONオブジェクトが連結されている場合に中間テキストも含まれる
2. 文字列内の `{` `}` を考慮していない
3. コードブロック形式を優先的に処理していない

**Decision**: 括弧バランス追跡 + コードブロック優先抽出で置き換え
**Rationale**: 既存のエラーケースを解決しつつ、パフォーマンス要件（10ms未満）を満たす
**Alternatives Considered**:
- JSONスキーマバリデーション → オーバーキル、標準ライブラリ外依存
- 正規表現のみ → ネストしたJSONで破綻

---

### 2. Bracket Balancing Algorithm

**Question**: 括弧バランス追跡の最適なアルゴリズムは？

**Findings**:
文字単位でスキャンし、以下の状態を追跡:
- `depth`: 現在のネスト深度（`{` で+1、`}` で-1）
- `in_string`: 文字列内かどうか
- `escape`: 次の文字がエスケープされているか

**Decision**: 文字単位スキャン + 状態機械
**Rationale**:
- O(n)の時間計算量、O(1)の空間計算量
- 標準ライブラリのみで実装可能
- 文字列内のエスケープ処理も正確

**Algorithm**:
```python
def extract_first_json(text: str) -> str | None:
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
```

---

### 3. Code Block Extraction

**Question**: Markdownコードブロックからの抽出方法は？

**Findings**:
LLMが返す可能性のあるフォーマット:
1. ` ```json\n{...}\n``` ` - jsonラベル付き
2. ` ```\n{...}\n``` ` - ラベルなし
3. ` ```json{...}``` ` - 改行なし

**Decision**: 正規表現で優先的に抽出
**Rationale**: コードブロック内のJSONはLLMが意図的にフォーマットしたもので、信頼性が高い

**Pattern**:
```python
import re
# DOTALLで改行をまたいでマッチ
CODE_BLOCK_PATTERN = re.compile(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```')
```

---

### 4. Error Handling Best Practices

**Question**: パースエラー時の最適なエラー情報は？

**Findings**:
デバッグに有用な情報:
- エラー位置（行番号、カラム番号）
- エラー周辺のコンテキスト（前後50文字程度）
- 抽出されたJSON文字列の長さ

**Decision**: エラー位置 + コンテキスト表示
**Rationale**: ユーザーがLLMの問題を特定しやすくなる

---

### 5. Performance Benchmarks

**Question**: 10ms未満のパフォーマンス目標は達成可能か？

**Findings**:
- 典型的なLLM応答: 500-2000文字
- Pythonの文字列スキャン: ~1M文字/秒
- 期待される処理時間: 1-2ms

**Decision**: パフォーマンス目標は十分達成可能
**Rationale**: アルゴリズムがO(n)、データサイズが小さい

---

## Summary

| 項目 | 決定 |
|------|------|
| アルゴリズム | 括弧バランス追跡 + 状態機械 |
| コードブロック | 正規表現で優先抽出 |
| エラー情報 | 位置 + コンテキスト |
| パフォーマンス | 目標達成可能（1-2ms予測） |

すべてのNEEDS CLARIFICATIONが解決済み。Phase 1へ進行可能。
