# Issue #33 Implementation Summary

## 作業概要
- Ollama ウォームアップ処理の統一を実装完了
- `call_ollama` 関数内で初回呼び出し時に自動ウォームアップを実行
- モジュールレベルの `set` で既にウォーム済みモデルを追跡

## 修正ファイル一覧

### 実装
- `src/obsidian_etl/utils/ollama.py`
  - `_warmed_models: set[str]` モジュールレベル変数追加
  - `_do_warmup(model, base_url)` ヘルパー関数追加
    - 最小限のリクエスト（num_predict=1）でモデルをロード
    - エラー時は警告ログを出力し例外は投げない
  - `call_ollama` 関数にウォームアップロジック追加
    - 初回呼び出し時のみ `_do_warmup` を実行
    - 2回目以降はスキップ

### テスト
- `tests/utils/test_ollama_warmup.py` (新規)
  - `TestOllamaWarmup`: `call_ollama` のウォームアップ動作を検証
    - `test_warmup_called_on_first_invocation`: 初回呼び出し時に warmup が実行される
    - `test_warmup_skipped_on_second_invocation`: 2回目以降はスキップされる
    - `test_warmup_per_model`: 異なるモデルは個別にウォームアップされる
  - `TestDoWarmup`: `_do_warmup` 関数の単体テスト
    - `test_warmup_sends_minimal_request`: 最小限のリクエストを送信する
    - `test_warmup_handles_failure_gracefully`: エラー時に例外を投げない

## テスト結果
- `make test`: 411 tests passed (18.138s)
- `make lint`: All checks passed (ruff + pylint: 10.00/10)

## 実装の特徴

### 自動ウォームアップ
- ユーザーは何もする必要なし
- `call_ollama` を呼ぶだけで自動的にウォームアップされる
- モデルごとに1回だけ実行（メモリ効率的）

### エラーハンドリング
- ウォームアップ失敗時も例外を投げず処理を継続
- 警告ログで失敗を記録
- 本番リクエストには影響しない

### テスト容易性
- モジュールレベルの `_warmed_models` は `setUp` でクリア可能
- モック使用で実際の Ollama 接続なしにテスト可能

## 次フェーズで対応予定
- `organize/nodes.py` の `_warmup_model` 関数削除（重複排除）
- 既存コードのリファクタリング

## 注意点
- `_warmed_models` はプロセスライフタイム全体で保持
- 異なるモデルを大量に使用する場合はメモリ使用量に注意
  （通常は2-3モデル程度なので問題なし）
