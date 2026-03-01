# Research: ウォームアップ失敗時に処理を停止する

**Date**: 2026-02-25
**Feature**: 062-warmup-fail-stop

## 調査項目

### R1: 現在のウォームアップ処理の動作

**調査結果**:

- **場所**: `src/obsidian_etl/utils/ollama.py:21-47`
- **動作**: `_do_warmup` 関数が例外をキャッチし、WARNING を出力して処理継続
- **問題**: `_warmed_models.add(model)` が失敗後も実行され、リトライなし

```python
# 現在のコード (ollama.py:46-47)
except Exception as e:
    logger.warning(f"Model warmup failed: {model}: {e}")
```

**影響範囲**:
- `call_ollama` は warmup 後に LLM 呼び出しを試行
- モデル未ロード状態で空レスポンス → JSON パースエラー

### R2: 終了コードの既存定義

**調査結果**:

CLAUDE.md より:

| Code | 意味 |
|------|------|
| 0 | 成功 |
| 1 | 一般エラー |
| 2 | 入力ファイル未発見 |
| 3 | Ollama 接続エラー |
| 4 | 部分成功 |
| 5 | 全件失敗 |

**決定**: 終了コード 3 を使用（既存定義に適合）

### R3: Kedro のエラーハンドリングパターン

**調査結果**:

- `hooks.py` に `ErrorHandlerHook` が存在
- `on_node_error` フックでノードエラーをキャッチ可能
- `PreRunValidationHook` で事前チェック（Ollama 接続確認）を実施中

**既存パターン**:
```python
# hooks.py:72-79
except (urllib.error.URLError, TimeoutError):
    logger.error("❌ Error: Ollama is not running")
    sys.exit(1)
```

**決定**: 同様のパターンで終了コード 3 を返す

### R4: カスタム例外の設計

**調査結果**:

Python のカスタム例外ベストプラクティス:
1. `Exception` を継承
2. 意味のある名前を付ける
3. コンテキスト情報を保持

**決定**:
```python
class OllamaWarmupError(Exception):
    """Raised when Ollama model warmup fails."""
    def __init__(self, model: str, reason: str):
        self.model = model
        self.reason = reason
        super().__init__(f"Model warmup failed: {model}: {reason}")
```

### R5: テスト戦略

**調査結果**:

- 既存テスト: `tests/test_ollama.py`（存在する場合）
- タイムアウトのモック: `unittest.mock.patch` で `urllib.request.urlopen`

**決定**:
1. `_do_warmup` のユニットテスト（タイムアウト、接続エラー）
2. `call_ollama` の統合テスト（warmup 失敗時の例外伝播）
3. フックのテスト（終了コード 3 の確認）

## まとめ

| 項目 | 決定 | 根拠 |
|------|------|------|
| 例外クラス | `OllamaWarmupError` | 明確な名前、コンテキスト保持 |
| 例外発生場所 | `_do_warmup` 内 | 一元化、テスト容易 |
| キャッチ場所 | `ErrorHandlerHook` | Kedro パターン準拠 |
| 終了コード | 3 | 既存定義（Ollama 接続エラー）|
| ログレベル | ERROR | 処理停止を伴うため |
