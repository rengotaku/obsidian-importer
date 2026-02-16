# Phase 4 RED Tests

## サマリー
- Phase: Phase 4 - User Story 3: extract_topic の統一実装
- FAIL テスト数: 4
- テストファイル: tests/pipelines/organize/test_nodes.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/pipelines/organize/test_nodes.py | test_extract_topic_uses_config | `_extract_topic_via_llm` が `get_ollama_config(params, "extract_topic")` を呼び出す |
| tests/pipelines/organize/test_nodes.py | test_extract_topic_uses_correct_model | 設定されたモデル（llama3.2:3b）が API 呼び出しで使用される |
| tests/pipelines/organize/test_nodes.py | test_extract_topic_uses_correct_timeout | 設定されたタイムアウト（30秒）が API 呼び出しで使用される |
| tests/pipelines/organize/test_nodes.py | test_extract_topic_num_predict_applied | `num_predict: 64` が Ollama API に渡される |

## テストクラス

### TestExtractTopicUsesOllamaConfig

`extract_topic` 関数が `get_ollama_config` と `call_ollama` を使用して
統一されたパラメーター管理を行うことを検証するテストクラス。

#### テストメソッド詳細

1. **test_extract_topic_uses_config**
   - `_extract_topic_via_llm` が `get_ollama_config(params, "extract_topic")` を呼び出すことを検証
   - モック: `get_ollama_config`, `call_ollama`
   - 期待: `get_ollama_config.assert_called_once_with(params, "extract_topic")`

2. **test_extract_topic_uses_correct_model**
   - `ollama.functions.extract_topic.model` のモデルが使用されることを検証
   - 設定: `functions.extract_topic.model = "llama3.2:3b"`
   - 期待: `call_ollama(..., model="llama3.2:3b")`

3. **test_extract_topic_uses_correct_timeout**
   - `ollama.functions.extract_topic.timeout` のタイムアウトが使用されることを検証
   - 設定: `functions.extract_topic.timeout = 30`
   - 期待: `call_ollama(..., timeout=30)`

4. **test_extract_topic_num_predict_applied**
   - `ollama.functions.extract_topic.num_predict` が Ollama API に渡されることを検証
   - 設定: `functions.extract_topic.num_predict = 64`
   - 期待: `call_ollama(..., num_predict=64)`

## 実装ヒント

1. `src/obsidian_etl/pipelines/organize/nodes.py` に以下をインポート:
   ```python
   from obsidian_etl.utils.ollama_config import get_ollama_config
   from obsidian_etl.utils.ollama import call_ollama
   ```

2. `_extract_topic_via_llm` を以下のように変更:
   ```python
   def _extract_topic_via_llm(content: str, params: dict) -> str | None:
       config = get_ollama_config(params, "extract_topic")

       # プロンプト構築
       system_prompt = "あなたはトピック分類の専門家です。..."
       user_message = f"会話内容:\n{body[:1000]}\n\n主題を1-3単語で答えてください。"

       response, error = call_ollama(
           system_prompt,
           user_message,
           model=config.model,
           base_url=config.base_url,
           timeout=config.timeout,
           temperature=config.temperature,
           num_predict=config.num_predict,
       )

       if error:
           logger.warning(f"Failed to extract topic: {error}")
           return None

       return response.strip()
   ```

3. 現在の実装（`requests.post` 直接呼び出し）を `call_ollama` に置き換える

## FAIL 出力例

```
ERROR: test_extract_topic_uses_config (tests.pipelines.organize.test_nodes.TestExtractTopicUsesOllamaConfig)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/pipelines/organize/test_nodes.py", line 1245, in test_extract_topic_uses_config
    with patch("obsidian_etl.pipelines.organize.nodes.get_ollama_config") as mock_get_config:
AttributeError: <module 'obsidian_etl.pipelines.organize.nodes'> does not have the attribute 'get_ollama_config'

ERROR: test_extract_topic_uses_correct_model (tests.pipelines.organize.test_nodes.TestExtractTopicUsesOllamaConfig)
----------------------------------------------------------------------
AttributeError: <module 'obsidian_etl.pipelines.organize.nodes'> does not have the attribute 'call_ollama'

ERROR: test_extract_topic_uses_correct_timeout (tests.pipelines.organize.test_nodes.TestExtractTopicUsesOllamaConfig)
----------------------------------------------------------------------
AttributeError: <module 'obsidian_etl.pipelines.organize.nodes'> does not have the attribute 'call_ollama'

ERROR: test_extract_topic_num_predict_applied (tests.pipelines.organize.test_nodes.TestExtractTopicUsesOllamaConfig)
----------------------------------------------------------------------
AttributeError: <module 'obsidian_etl.pipelines.organize.nodes'> does not have the attribute 'call_ollama'

----------------------------------------------------------------------
Ran 337 tests in 1.179s

FAILED (errors=4)
```

## 失敗原因

現在の `_extract_topic_via_llm` 実装:
- `requests.post` を直接使用して `/api/generate` を呼び出している
- `get_ollama_config` をインポート/使用していない
- `call_ollama` をインポート/使用していない
- `num_predict` パラメーターを API に渡していない

これらのテストは、実装が `call_ollama` と `get_ollama_config` を使用するように
リファクタリングされた後に PASS する。
