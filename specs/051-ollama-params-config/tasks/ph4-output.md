# Phase 4 Output

## 作業概要
- Phase 4 - User Story 3: extract_topic の統一実装の実装完了
- FAIL テスト 4 件を PASS させた

## 修正ファイル一覧
- `src/obsidian_etl/pipelines/organize/nodes.py` - `_extract_topic_via_llm()` を `get_ollama_config` と `call_ollama` を使用するようリファクタリング

## 実装内容

### 1. インポート追加

`src/obsidian_etl/pipelines/organize/nodes.py` に以下をインポート:

```python
from obsidian_etl.utils.ollama import call_ollama
from obsidian_etl.utils.ollama_config import get_ollama_config
```

### 2. `_extract_topic_via_llm()` のリファクタリング

**変更前**:
- `requests.post` を直接使用して `/api/generate` エンドポイントを呼び出し
- `params["ollama"]` から直接パラメーターを取得
- `num_predict` パラメーターを API に渡していない

**変更後**:
- `get_ollama_config(params, "extract_topic")` で関数別設定を取得
- `call_ollama()` を使用して API を呼び出し
- `config.num_predict` を含むすべてのパラメーターを API に渡す
- システムプロンプトとユーザーメッセージを分離（`call_ollama` の仕様に合わせる）

### 3. テスト結果

```bash
$ make test
...
Ran 337 tests in 9.124s

OK

✅ All tests passed
```

**PASS したテスト**:
- `test_extract_topic_uses_config`: `get_ollama_config(params, "extract_topic")` が呼び出されること
- `test_extract_topic_uses_correct_model`: 設定されたモデル（llama3.2:3b）が使用されること
- `test_extract_topic_uses_correct_timeout`: 設定されたタイムアウト（30秒）が使用されること
- `test_extract_topic_num_predict_applied`: `num_predict: 64` が Ollama API に渡されること

## 注意点

### 次 Phase で必要な情報

Phase 5 では、既存の `extract_knowledge` と `translate_summary` 関数も同様に `get_ollama_config` と `call_ollama` を使用するようリファクタリングを行う。

### プロンプト形式の変更

`call_ollama` は `system_prompt` と `user_message` を分離した形式を要求するため、従来の単一プロンプト形式から変更が必要だった。

**変更前**:
```python
prompt = f"""この会話から主題（トピック）を1つ抽出してください。

会話内容:
{body[:1000]}

主題をカテゴリレベル（1-3単語）で答えてください。
..."""
```

**変更後**:
```python
system_prompt = """あなたはトピック分類の専門家です。会話内容から主題を1つ抽出してください。
..."""

user_message = f"""会話内容:
{body[:1000]}

主題を1-3単語で答えてください。"""
```

### エラーハンドリングの改善

`call_ollama` は `(response, error)` のタプルを返すため、エラーハンドリングが簡潔になった。

**変更前**:
```python
try:
    response = requests.post(...)
    response.raise_for_status()
    result = response.json()
    topic = result.get("response", "").strip()
    return topic if topic else None
except Exception as e:
    logger.warning(f"Failed to extract topic via LLM: {e}")
    return None
```

**変更後**:
```python
response, error = call_ollama(...)

if error:
    logger.warning(f"Failed to extract topic via LLM: {error}")
    return None

topic = response.strip()
return topic if topic else None
```

## 実装のミス・課題

特になし。

すべてのテストが PASS し、コードの可読性とメンテナンス性が向上した。
