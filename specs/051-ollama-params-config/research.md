# Research: Ollama パラメーター関数別設定

**Feature**: 051-ollama-params-config
**Date**: 2026-02-15

## Research Topics

1. Kedro parameters.yml のネスト構造
2. 既存 Ollama パラメーター取得パターン
3. extract_topic の現在の実装
4. Ollama API パラメーター

---

## 1. Kedro parameters.yml のネスト構造

### Finding

Kedro の `parameters.yml` は任意のネスト構造をサポート。ノードは `params:` 引数で dict として受け取る。

現在の構造:
```yaml
import:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    max_retries: 3

organize:
  ollama:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 60
```

### Decision

`ollama` セクションをトップレベルに移動し、`defaults` + `functions` の2層構造に変更:

```yaml
ollama:
  defaults:
    model: "gemma3:12b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1
  functions:
    extract_knowledge:
      num_predict: 16384  # 長文出力用
    translate_summary:
      num_predict: 1024   # 中程度出力
    extract_topic:
      num_predict: 64     # 短い出力（1-3単語）
      model: "llama3.2:3b"  # 軽量モデルで十分
```

### Rationale

- **defaults**: 全関数で共通の基本設定
- **functions**: 関数ごとのオーバーライド（部分指定可）
- トップレベル配置により `import`/`organize` 間での重複を排除

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| `import.ollama.extract_knowledge` | パイプライン間で設定が分散 |
| フラットキー `ollama_extract_knowledge` | 構造が不明確 |
| 関数名を直接キーに `extract_knowledge.model` | defaults との関係が曖昧 |

---

## 2. 既存 Ollama パラメーター取得パターン

### Finding

現在の実装箇所:

| File | Function | 取得方法 |
|------|----------|----------|
| `knowledge_extractor.py` | `extract_knowledge()` | `params.get("ollama", {})` |
| `knowledge_extractor.py` | `translate_summary()` | `params.get("ollama", {})` |
| `organize/nodes.py` | `_extract_topic_via_llm()` | `params.get("ollama", {})` |

共通パターン:
```python
ollama_params = params.get("ollama", {})
model = ollama_params.get("model", "gemma3:12b")
base_url = ollama_params.get("base_url", "http://localhost:11434")
# ... 各パラメーター取得
```

### Decision

統一ヘルパー関数 `get_ollama_config(params, function_name)` を作成:

```python
def get_ollama_config(params: dict, function_name: str) -> dict:
    """Get Ollama config for a specific function.

    Merges defaults with function-specific overrides.

    Args:
        params: Pipeline params containing ollama section.
        function_name: One of "extract_knowledge", "translate_summary", "extract_topic".

    Returns:
        Dict with model, base_url, timeout, temperature, num_predict.
    """
```

### Rationale

- 取得ロジックの一元化
- デフォルト値のフォールバック処理を統一
- テスト容易性（モック対象が明確）
- 関数名の typo を検出可能に（バリデーション追加可能）

---

## 3. extract_topic の現在の実装

### Finding

`_extract_topic_via_llm()` の実装:

```python
# 現在: /api/generate エンドポイント使用
response = requests.post(
    f"{base_url}/api/generate",
    json={"model": model, "prompt": prompt, "stream": False},
    timeout=60,
)
```

`call_ollama()` の実装:

```python
# call_ollama: /api/chat エンドポイント使用
url = f"{base_url}/api/chat"
payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    "stream": False,
    "options": {"num_ctx": num_ctx, "num_predict": num_predict, "temperature": temperature},
}
```

### Differences

| 項目 | `_extract_topic_via_llm` | `call_ollama` |
|------|--------------------------|---------------|
| エンドポイント | `/api/generate` | `/api/chat` |
| 入力形式 | `prompt` (単一文字列) | `messages` (role/content) |
| options | なし | `num_ctx`, `num_predict`, `temperature` |
| エラーハンドリング | 簡易 | 詳細（タイムアウト、接続エラー、JSONパースエラー） |

### Decision

`_extract_topic_via_llm` を `call_ollama` を使用する実装に変更。

### Implementation Approach

```python
def _extract_topic_via_llm(content: str, params: dict) -> str | None:
    config = get_ollama_config(params, "extract_topic")

    # プロンプトを system/user に分離
    system_prompt = "あなたはトピック分類の専門家です。..."
    user_message = f"会話内容:\n{content[:1000]}\n\n主題を1-3単語で答えてください。"

    response, error = call_ollama(
        system_prompt,
        user_message,
        model=config["model"],
        base_url=config["base_url"],
        timeout=config["timeout"],
        temperature=config["temperature"],
        num_predict=config["num_predict"],
    )

    if error:
        logger.warning(f"Failed to extract topic: {error}")
        return None

    return response.strip()
```

---

## 4. Ollama API パラメーター

### Finding

Ollama `/api/chat` でサポートされる `options`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_ctx` | int | 2048 | コンテキストウィンドウサイズ |
| `num_predict` | int | -1 | 最大出力トークン数（-1 = 無制限） |
| `temperature` | float | 0.8 | サンプリング温度 |
| `top_p` | float | 0.9 | Nucleus sampling |
| `top_k` | int | 40 | Top-k sampling |
| `repeat_penalty` | float | 1.1 | 繰り返しペナルティ |

### Decision

本機能で設定可能にするパラメーター:

| Parameter | 設定可能 | Reason |
|-----------|---------|--------|
| `model` | ✅ | 関数ごとに異なるモデルを使用 |
| `base_url` | ✅ | 環境ごとの切り替え |
| `timeout` | ✅ | 長文処理でタイムアウト延長 |
| `temperature` | ✅ | 出力の determinism 調整 |
| `num_predict` | ✅ | 出力長制御（最重要） |
| `num_ctx` | ❌ | 全関数で共通で十分 |
| `top_p`, `top_k` | ❌ | 通常不要 |

### Rationale

- `num_predict` が最重要（出力途切れ防止、トークン節約）
- `model` は `extract_topic` で軽量モデル使用に有用
- その他は高度な調整用で通常不要

---

## Summary

| Topic | Decision |
|-------|----------|
| YAML構造 | `ollama.defaults` + `ollama.functions.{関数名}` |
| パラメーター取得 | `get_ollama_config(params, function_name)` ヘルパー |
| extract_topic | `call_ollama` 使用に変更 |
| 設定可能パラメーター | model, base_url, timeout, temperature, num_predict |
