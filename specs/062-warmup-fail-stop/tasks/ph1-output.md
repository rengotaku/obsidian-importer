# Phase 1 Output: Setup

**Date**: 2026-02-25
**Status**: Completed

## Executed Tasks

- [x] T001 Read: src/obsidian_etl/utils/ollama.py（現在の _do_warmup 実装確認）
- [x] T002 Read: src/obsidian_etl/hooks.py（ErrorHandlerHook 確認）
- [x] T003 Read: tests/ 配下の既存テスト構造確認
- [x] T004 Edit: specs/062-warmup-fail-stop/tasks/ph1-output.md（セットアップ分析結果）

## Existing Code Analysis

### src/obsidian_etl/utils/ollama.py

**Structure**:
- `_warmed_models: set[str]`: モジュールレベルのウォームアップ済みモデル追跡
- `_do_warmup(model, base_url)`: ウォームアップ実行（現在は失敗時 WARNING のみ）
- `call_ollama(...)`: LLM 呼び出し、初回使用時に warmup 実行

**Current Implementation (lines 46-47)**:
```python
except Exception as e:
    logger.warning(f"Model warmup failed: {model}: {e}")
```

**Required Updates**:
1. **新規例外クラス追加**: `OllamaWarmupError(Exception)` - model, reason を保持
2. **_do_warmup 修正**: WARNING → ERROR、例外を raise（catch せず）
3. **call_ollama 修正**: `_warmed_models.add(model)` を warmup 成功後のみに移動

**Implementation Location**:
- 例外クラス: logger 定義後（line 16 付近）
- _do_warmup: lines 21-47 を修正

### src/obsidian_etl/hooks.py

**Structure**:
- `PreRunValidationHook`: パイプライン開始前の検証（Ollama 接続チェックあり）
- `ErrorHandlerHook`: ノードエラーハンドリング（現在は単純なログ出力のみ）
- `LoggingHook`: 実行時間ログ

**Current Implementation (lines 138-151)**:
```python
class ErrorHandlerHook:
    @hook_impl
    def on_node_error(self, error, node, catalog, inputs, is_async):
        logger.error(f"Node '{node}' failed: {error}")
```

**Required Updates**:
1. `OllamaWarmupError` をインポート
2. `on_node_error` で `OllamaWarmupError` を個別ハンドリング
3. 終了コード 3 で `sys.exit(3)` 呼び出し
4. モデル名・推奨アクションを含むエラーメッセージ出力

**Existing Pattern (lines 72-79)**:
```python
# PreRunValidationHook での Ollama エラー処理パターン
except (urllib.error.URLError, TimeoutError):
    logger.error("❌ Error: Ollama is not running")
    sys.exit(1)
```

## Existing Test Analysis

### tests/utils/test_ollama_warmup.py

**Coverage**:
- `TestOllamaWarmup`: warmup 呼び出しタイミングのテスト
- `TestDoWarmup`: _do_warmup の動作テスト

**Critical Test (line 158-174)**:
```python
def test_warmup_handles_failure_gracefully(self, mock_urlopen):
    """_do_warmup がエラー時に例外を投げずに警告ログを出すこと。"""
```
→ **この動作を変更**: 例外を raise するようになるため、このテストは削除 or 修正が必要

### tests/test_hooks.py

**Coverage**: 既存のフックテスト（新規 warmup エラーハンドリングのテストは存在しない）

### New Test Files Required

1. **tests/test_warmup_error.py**:
   - `OllamaWarmupError` 例外クラスのテスト
   - `_do_warmup` のタイムアウト時例外発生テスト
   - `_do_warmup` の接続エラー時例外発生テスト
   - `call_ollama` の例外伝播テスト

2. **tests/test_hooks_warmup.py**:
   - `ErrorHandlerHook` の `OllamaWarmupError` ハンドリングテスト
   - 終了コード 3 のテスト
   - エラーメッセージ内容のテスト

## Technical Decisions

1. **例外定義場所**: `ollama.py` 内に定義（モジュール固有の例外）
2. **例外に含める情報**: `model` と `reason` を属性として保持（hooks でのメッセージ生成に使用）
3. **タイムアウト検出**: `TimeoutError` を個別キャッチして明確なメッセージ
4. **既存テストへの影響**: `test_warmup_handles_failure_gracefully` は動作変更のため削除が必要

## Handoff to Next Phase

### Phase 2 (US1: ウォームアップ失敗時の即時停止)

実装対象:
- `OllamaWarmupError` 例外クラス
- `_do_warmup` の修正（WARNING → ERROR + raise）
- `call_ollama` の `_warmed_models.add` 位置修正

再利用可能コード:
- 既存の `_do_warmup` 構造をベースに修正
- urllib エラーハンドリングパターン

注意点:
- `tests/utils/test_ollama_warmup.py:158-174` の既存テスト `test_warmup_handles_failure_gracefully` は新動作と矛盾するため、削除または修正が必要

### Phase 3 (US2: 明確なエラーメッセージの表示)

実装対象:
- `ErrorHandlerHook.on_node_error` の修正
- `OllamaWarmupError` インポートと個別ハンドリング
- 終了コード 3 + 推奨アクション出力

再利用可能コード:
- `PreRunValidationHook._check_ollama` のエラーメッセージフォーマット
- `sys.exit(1)` → `sys.exit(3)` パターン
