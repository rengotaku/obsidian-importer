# Phase 5 Output

## 作業概要
- Phase 5 - Integration - 既存関数への適用 の実装完了
- FAIL テスト 4 件を PASS させた
- `extract_knowledge` と `translate_summary` が `get_ollama_config` 経由でパラメーター取得

## 修正ファイル一覧
- `src/obsidian_etl/utils/knowledge_extractor.py` - `get_ollama_config` 統合

## 実装内容

### 1. Import 追加

`knowledge_extractor.py` に `get_ollama_config` をインポート:

```python
from obsidian_etl.utils.ollama_config import get_ollama_config
```

### 2. extract_knowledge() の変更

**変更前**:
```python
def extract_knowledge(..., params: dict) -> tuple[dict | None, str | None]:
    ...
    ollama_params = params.get("ollama", {})

    response, error = call_ollama(
        prompt,
        user_message,
        model=ollama_params.get("model", "gemma3:12b"),
        base_url=ollama_params.get("base_url", "http://localhost:11434"),
        num_predict=ollama_params.get("num_predict", -1),
        timeout=ollama_params.get("timeout", 120),
        temperature=ollama_params.get("temperature", 0.2),
    )
```

**変更後**:
```python
def extract_knowledge(..., params: dict) -> tuple[dict | None, str | None]:
    ...
    config = get_ollama_config(params, "extract_knowledge")

    response, error = call_ollama(
        prompt,
        user_message,
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )
```

### 3. translate_summary() の変更

**変更前**:
```python
def translate_summary(summary: str, params: dict) -> tuple[str | None, str | None]:
    ...
    ollama_params = params.get("ollama", {})

    response, error = call_ollama(
        prompt,
        f"以下の英語サマリーを日本語に翻訳してください:\n\n{summary}",
        model=ollama_params.get("model", "gemma3:12b"),
        base_url=ollama_params.get("base_url", "http://localhost:11434"),
        num_predict=ollama_params.get("num_predict", -1),
        timeout=ollama_params.get("timeout", 120),
        temperature=ollama_params.get("temperature", 0.2),
    )
```

**変更後**:
```python
def translate_summary(summary: str, params: dict) -> tuple[str | None, str | None]:
    ...
    config = get_ollama_config(params, "translate_summary")

    response, error = call_ollama(
        prompt,
        f"以下の英語サマリーを日本語に翻訳してください:\n\n{summary}",
        model=config.model,
        base_url=config.base_url,
        num_predict=config.num_predict,
        timeout=config.timeout,
        temperature=config.temperature,
    )
```

## テスト結果

### 全テスト成功

```
Ran 341 tests in 5.498s

OK

✅ All tests passed
```

### GREEN テスト詳細

Phase 5 で追加された 4 件の FAIL テストがすべて PASS:

| Test Class | Test Method | Status |
|-----------|-------------|--------|
| TestExtractKnowledgeUsesOllamaConfig | test_extract_knowledge_uses_config | PASS ✅ |
| TestExtractKnowledgeUsesOllamaConfig | test_extract_knowledge_num_predict_applied | PASS ✅ |
| TestTranslateSummaryUsesOllamaConfig | test_translate_summary_uses_config | PASS ✅ |
| TestTranslateSummaryUsesOllamaConfig | test_translate_summary_num_predict_applied | PASS ✅ |

## 機能検証

### extract_knowledge の動作

1. `get_ollama_config(params, "extract_knowledge")` を呼び出し
2. 関数別設定から `num_predict=16384`, `timeout=300` を取得
3. `call_ollama()` に適切なパラメーターを渡す

### translate_summary の動作

1. `get_ollama_config(params, "translate_summary")` を呼び出し
2. 関数別設定から `num_predict=1024` を取得
3. `call_ollama()` に適切なパラメーターを渡す

## リファクタリング効果

### Before (直接 params アクセス)

- ハードコードされたデフォルト値 (`"gemma3:12b"`, `120`, `0.2`)
- 関数別設定の仕組みなし
- `num_predict` のデフォルトが `-1` (無制限)

### After (get_ollama_config 統合)

- `parameters.yml` の `ollama.defaults` から一元管理
- `ollama.functions.<function_name>` で関数別設定をオーバーライド
- `num_predict` を関数ごとに適切な値に設定可能
  - `extract_knowledge`: 16384 (長文ナレッジ抽出)
  - `translate_summary`: 1024 (短文翻訳)
  - `extract_topic`: 512 (トピック抽出)

## 統合完了状況

全 LLM 呼び出し関数が `get_ollama_config` 経由でパラメーター取得:

| 関数 | ファイル | Status |
|------|---------|--------|
| `extract_knowledge` | `utils/knowledge_extractor.py` | ✅ 統合完了 (Phase 5) |
| `translate_summary` | `utils/knowledge_extractor.py` | ✅ 統合完了 (Phase 5) |
| `extract_topic` | `pipelines/organize/nodes.py` | ✅ 統合完了 (Phase 4) |

## 注意点

### 後方互換性

- 既存の `import.ollama` 構造も引き続きサポート
- `get_ollama_config` は自動的に以下の順序でパラメーター取得:
  1. `ollama.functions.<function_name>` (関数別設定)
  2. `ollama.defaults` (共通デフォルト)
  3. `import.ollama` / `organize.ollama` (レガシー)
  4. `HARDCODED_DEFAULTS` (コード内デフォルト)

### 次 Phase への引き継ぎ

Phase 6 (Polish) で実施予定:
- レガシー構造 (`import.ollama`, `organize.ollama`) の削除検討
- `get_ollama_config()` のマージロジックに関する docstring 追加
- `organize/nodes.py` の不要な `requests` import 削除検討
- quickstart.md の設定例の動作確認

## 実装のミス・課題

なし。すべてのテストが PASS し、関数別パラメーター設定が期待通り動作。
