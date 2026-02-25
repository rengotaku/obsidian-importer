# Quickstart: ウォームアップ失敗時に処理を停止する

## 概要

このドキュメントは、ウォームアップ失敗時の処理停止機能の実装ガイドです。

## 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/obsidian_etl/utils/ollama.py` | 例外クラス追加、`_do_warmup` 修正 |
| `src/obsidian_etl/hooks.py` | 例外ハンドリング追加 |
| `tests/test_warmup_error.py` | 新規テスト |

## 実装手順

### Step 1: カスタム例外の追加

`ollama.py` の先頭（logger 定義後）に追加:

```python
class OllamaWarmupError(Exception):
    """Raised when Ollama model warmup fails."""
    def __init__(self, model: str, reason: str):
        self.model = model
        self.reason = reason
        super().__init__(f"Model warmup failed: {model}: {reason}")
```

### Step 2: `_do_warmup` の修正

```python
def _do_warmup(model: str, base_url: str) -> None:
    """Simple ping to load model into memory.

    Raises:
        OllamaWarmupError: If warmup fails (timeout or connection error).
    """
    try:
        # ... 既存のリクエスト処理 ...
        logger.info(f"Model warmup completed: {model}")
    except TimeoutError as e:
        logger.error(f"Model warmup timed out: {model}")
        raise OllamaWarmupError(model, "timed out") from e
    except Exception as e:
        logger.error(f"Model warmup failed: {model}: {e}")
        raise OllamaWarmupError(model, str(e)) from e
```

### Step 3: `call_ollama` の修正

```python
# Warmup model on first use (raises OllamaWarmupError on failure)
if model not in _warmed_models:
    _do_warmup(model, base_url)  # 例外は伝播させる
    _warmed_models.add(model)  # 成功時のみ追加
```

### Step 4: フックの修正

`hooks.py` に追加:

```python
from obsidian_etl.utils.ollama import OllamaWarmupError

class ErrorHandlerHook:
    @hook_impl
    def on_node_error(self, error: Exception, node: object, ...) -> None:
        if isinstance(error, OllamaWarmupError):
            logger.error("")
            logger.error(f"❌ Error: Model warmup failed: {error.model}")
            logger.error("")
            logger.error("  Ollama モデルのウォームアップに失敗しました。")
            logger.error("  以下を確認してください:")
            logger.error("    1. Ollama サーバーが起動している (ollama serve)")
            logger.error(f"    2. モデルがダウンロード済み (ollama pull {error.model})")
            logger.error("")
            sys.exit(3)
        logger.error(f"Node '{node}' failed: {error}")
```

## テスト方法

```bash
# ユニットテスト
make test

# 手動テスト（Ollama 停止状態で）
ollama stop
kedro run  # 終了コード 3 で停止することを確認
echo $?    # 3 が出力される
```

## 検証ポイント

- [ ] ウォームアップ失敗時に ERROR ログが出力される
- [ ] 処理が即座に停止する（後続の LLM 呼び出しなし）
- [ ] 終了コード 3 が返される
- [ ] エラーメッセージにモデル名が含まれる
- [ ] エラーメッセージに推奨アクションが含まれる
