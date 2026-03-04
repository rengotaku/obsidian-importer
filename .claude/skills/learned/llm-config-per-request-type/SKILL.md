---
name: llm-config-per-request-type
description: "LLM設定は共有せず、リクエストの用途・出力サイズごとに専用設定を用意する"
---

# LLM Config Per Request Type

## Problem

複数のLLM呼び出しが同じ設定キーを共有すると、出力サイズが異なる用途で問題が発生する。

例: `extract_topic_and_genre` 設定を2つの関数で共有
- `_extract_topic_and_genre_via_llm()`: 短い出力（topic + genre）
- `_suggest_new_genres_via_llm()`: 長いJSON配列（最大3件の提案）

`num_predict: 512` は短い出力には十分だが、長いJSON配列は途中で切れて空レスポンスになる。

## Solution

LLMリクエストの用途ごとに専用の設定キーを用意する。

```yaml
# conf/base/parameters.yml
ollama:
  functions:
    # 短い出力用
    extract_topic_and_genre:
      num_predict: 512
      timeout: 120

    # 長いJSON出力用
    suggest_genres:
      num_predict: 4096
      timeout: 180
```

コード側で適切な設定キーを参照:

```python
# 短い出力
config = get_ollama_config(params, "extract_topic_and_genre")

# 長い出力
config = get_ollama_config(params, "suggest_genres")
```

## When to Use

- 新しいLLM呼び出しを追加するとき
- 既存のLLM呼び出しで空レスポンスや途中切れが発生したとき
- 同じ設定を複数の関数で共有しようとしているとき

## Checklist

新しいLLM関数を追加する際:

- [ ] 期待される出力サイズを見積もる
- [ ] 専用の設定キーを `parameters.yml` に追加
- [ ] `num_predict` を出力サイズに応じて設定
- [ ] `timeout` を処理時間に応じて設定
