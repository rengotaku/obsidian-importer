# Implementation Plan: ウォームアップ失敗時に処理を停止する

**Branch**: `062-warmup-fail-stop` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/062-warmup-fail-stop/spec.md`

## Summary

Ollama モデルのウォームアップがタイムアウトまたは失敗した場合、現在の WARNING ログを ERROR に変更し、カスタム例外を発生させてパイプラインを即座に停止する。終了コード 3（Ollama 接続エラー）を返すことで、CI/CD パイプラインでのエラー検出を可能にする。

## Technical Context

**Language/Version**: Python 3.11+（Python 3.13 compatible）
**Primary Dependencies**: Kedro 1.1.1, kedro-datasets, requests (urllib)
**Storage**: N/A
**Testing**: pytest（unittest スタイル）
**Target Platform**: Linux server
**Project Type**: single（Kedro パイプライン）
**Performance Goals**: ウォームアップ失敗から停止まで 1 秒以内
**Constraints**: 既存の終了コード体系（1-5）を維持
**Scale/Scope**: 単一ファイル修正（ollama.py）、フック追加（hooks.py）

## Constitution Check

*Constitution ファイルが存在しないため、プロジェクト規約（CLAUDE.md）に基づいてチェック*

| Gate | Status | Notes |
|------|--------|-------|
| 後方互換性 | ✅ PASS | 不要（プロジェクト方針：後方互換性は考慮しない）|
| シンプルさ | ✅ PASS | カスタム例外 1 つと hooks.py 修正のみ |
| 終了コード | ✅ PASS | 既存の終了コード 3 を使用 |

## Project Structure

### Documentation (this feature)

```text
specs/062-warmup-fail-stop/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── spec.md              # Feature specification
└── checklists/
    └── requirements.md  # Quality checklist
```

### Source Code (repository root)

```text
src/obsidian_etl/
├── utils/
│   └── ollama.py        # 修正対象：_do_warmup, 新規例外クラス
└── hooks.py             # 修正対象：例外ハンドリング追加

tests/
├── test_ollama.py       # 既存テストに追加
└── test_hooks.py        # 新規テスト
```

**Structure Decision**: 既存の Kedro プロジェクト構造を維持。`ollama.py` に例外クラスを追加し、`hooks.py` でキャッチして終了コード 3 を返す。

## Complexity Tracking

*Constitution Check に違反なし - 追跡不要*

## Implementation Phases

### Phase 1: カスタム例外の追加

1. `ollama.py` に `OllamaWarmupError` 例外クラスを追加
2. `_do_warmup` 関数で WARNING → ERROR に変更
3. `_do_warmup` 関数で例外を raise（catch せず）
4. `call_ollama` から `_warmed_models.add(model)` を warmup 成功時のみに変更

### Phase 2: フックでの例外ハンドリング

1. `hooks.py` の `ErrorHandlerHook` で `OllamaWarmupError` をキャッチ
2. 終了コード 3 で `sys.exit(3)` を呼び出し
3. エラーメッセージにモデル名と推奨アクションを含める

### Phase 3: テストの追加

1. `test_ollama.py` に warmup 失敗時の例外テスト追加
2. `test_hooks.py` に終了コードテスト追加

## Design Decisions

### D1: 例外の発生場所

**決定**: `_do_warmup` 内で例外を raise

**理由**:
- `call_ollama` は複数箇所から呼ばれる
- 例外を発生させる場所を一元化
- テストが容易

**却下した代替案**:
- `call_ollama` でエラータプルを返す → 呼び出し元全てで終了処理が必要

### D2: 例外のキャッチ場所

**決定**: `hooks.py` の `ErrorHandlerHook.on_node_error`

**理由**:
- Kedro のフック機構を活用
- 全ノードで一貫したエラーハンドリング
- 終了コード管理が集約

**却下した代替案**:
- 各ノード関数でキャッチ → 重複コード

### D3: 終了コード

**決定**: 終了コード 3（既存定義）

**理由**:
- CLAUDE.md で「Ollama 接続エラー」として定義済み
- CI/CD との一貫性維持
