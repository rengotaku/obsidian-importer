# Phase 1-3 Output

## 作業概要
- Issue#38 の実装完了
- Ollama モデルのデフォルト値 `gemma3:12b` を削除し、設定必須化を実現
- 全テスト (411 tests) がパス
- Lint チェック (ruff + pylint) がパス

## 修正ファイル一覧

### Phase 1: コア実装
- `src/obsidian_etl/utils/ollama_config.py`
  - `OllamaConfig.model` のデフォルト値を削除（型注釈のみ: `model: str`）
  - `HARDCODED_DEFAULTS` から `"model"` エントリを削除
  - docstring 内のサンプルコードを更新（`gemma3:12b` → `gpt-oss:20b`）

- `src/obsidian_etl/utils/ollama.py`
  - `call_ollama()` の `model` 引数からデフォルト値を削除（必須引数化）

### Phase 2: テスト更新
- `tests/utils/test_ollama_config.py`
  - `test_ollama_config_defaults`: `model` 引数を明示的に指定
  - `test_empty_params_returns_hardcoded_defaults`: model なしで TypeError を期待するよう変更
  - `test_empty_ollama_section_returns_hardcoded_defaults`: 同上
  - `test_partial_defaults_merge`: `model` と `timeout` を指定
  - `test_partial_function_override`: `model` を defaults に追加
  - `test_timeout_at_boundary_valid`: `model` を明示的に指定
  - `test_temperature_at_boundary_valid`: `model` を明示的に指定

- `tests/utils/test_ollama_warmup.py`
  - 既に `model="gemma3:12b"` を明示的に指定済み（変更不要）

- `tests/pipelines/transform/test_nodes.py`
  - `_make_params()`: ollama 設定を `defaults` 構造に変更

- `tests/pipelines/organize/test_nodes.py`
  - `_make_organize_params()`: ollama 設定を `defaults` 構造で追加
  - 重複する `params["ollama"]` 代入を削除（8箇所）
  - `_suggest_new_genres_via_llm` 関連テスト: ollama 設定を `defaults` 構造に変更（3箇所）

- `tests/test_integration.py`
  - `params:import`: ollama 設定を `defaults` 構造に変更（4箇所）
  - `params:organize`: ollama 設定を `defaults` 構造で追加（4箇所）

### Phase 3: 検証
- 全テスト (411 tests) がパス
- Lint チェック (ruff + pylint: 10.00/10.00) がパス

## 注意点

### 本番環境への影響
- `conf/base/parameters.yml` で `ollama.defaults.model` の設定が必須
- 設定なしで実行すると `TypeError: OllamaConfig.__init__() missing 1 required positional argument: 'model'` が発生

### 推奨設定例
```yaml
ollama:
  defaults:
    model: "gpt-oss:20b"
    base_url: "http://localhost:11434"
    timeout: 120
    temperature: 0.2
    num_predict: -1
  functions:
    extract_knowledge:
      num_predict: 16384
      timeout: 300
    translate_summary:
      num_predict: 1024
```

## 実装のミス・課題
なし

## 次 Phase への引き継ぎ
なし（Issue#38 完結）
