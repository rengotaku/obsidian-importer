# Phase 1 Output: Setup (Project Initialization)

## Summary

Kedro 1.1.1 プロジェクトの初期化を完了。既存の `src/etl/` から utils をリファクタ移植し、パイプラインスケルトン、設定ファイル、テストディレクトリを作成。

## Completed Tasks

- [X] T001-T006: 既存実装の読み込み・理解
- [X] T007: Kedro プロジェクト構造を手動作成（`kedro info` で認識確認済み）
- [X] T008: `kedro==1.1.1`, `kedro-datasets` インストール済み
- [X] T009: `conf/base/catalog.yml` 作成（PartitionedDataset 定義）
- [X] T010: `conf/base/parameters.yml` 作成（Ollama/Organize パラメータ）
- [X] T011: `conf/base/logging.yml` 作成
- [X] T012: `ollama.py` 移植（純粋関数インターフェース、params dict 入力）
- [X] T013: `knowledge_extractor.py` 移植（関数ベース API）
- [X] T014: `chunker.py` 移植（dict ベースメッセージ、ChunkInfo dataclass）
- [X] T015: `file_id.py` 移植（str パス入力に変更）
- [X] T016-T017: プロンプトテンプレートコピー
- [X] T018: パイプラインスケルトンディレクトリ作成（5 パイプライン）
- [X] T019: `hooks.py` 作成（ErrorHandlerHook, LoggingHook）
- [X] T020: `pipeline_registry.py` 作成（プレースホルダー）
- [X] T021: `settings.py` 作成（Hook 登録）
- [X] T022: `data/` ディレクトリ構造作成
- [X] T023: `tests/` ディレクトリ構造作成（conftest.py 含む）
- [X] T024: Makefile に `kedro-run`, `kedro-test`, `kedro-viz` 追加
- [X] T025: `kedro info` 正常動作確認
- [X] T026: Phase 出力生成

## Files Created/Modified

### New Files
- `src/obsidian_etl/__init__.py`
- `src/obsidian_etl/settings.py`
- `src/obsidian_etl/pipeline_registry.py`
- `src/obsidian_etl/hooks.py`
- `src/obsidian_etl/pipelines/` (5 pipelines with __init__.py, nodes.py, pipeline.py)
- `src/obsidian_etl/utils/ollama.py`
- `src/obsidian_etl/utils/knowledge_extractor.py`
- `src/obsidian_etl/utils/chunker.py`
- `src/obsidian_etl/utils/file_id.py`
- `src/obsidian_etl/utils/prompts/knowledge_extraction.txt`
- `src/obsidian_etl/utils/prompts/summary_translation.txt`
- `conf/base/catalog.yml`
- `conf/base/parameters.yml`
- `conf/base/logging.yml`
- `tests/conftest.py`
- `tests/pipelines/` (5 pipeline test dirs with test_nodes.py)
- `data/` (4 layers with subdirectories)

### Modified Files
- `pyproject.toml` (Kedro config, dependencies, coverage)
- `Makefile` (Kedro targets)
- `.gitignore` (data/, logs/, conf/local/)

## Key Decisions

1. **Manual project creation**: `kedro new` は対話的でサブディレクトリを作成するため、既存リポジトリに手動で構造を構築
2. **Hook signature fix**: Kedro 1.1.1 の `on_node_error` は `session_id` パラメータを受け付けないため、仕様から除外
3. **Utils refactoring**: Protocol/class ベースを純粋関数 + dict ベースに変換（Kedro ノードの入出力パターンに適合）
4. **chunker.py**: `ConversationProtocol` → `list[dict]` 入力に変更（PartitionedDataset の dict パターン対応）
5. **file_id.py**: `Path` 入力 → `str` 入力に変更（JSON シリアライズ容易化）

## Verification

- `kedro info` ✅ プロジェクト認識
- `kedro run` → `ValueError: Pipeline contains no nodes` ✅ 空パイプラインの期待通りの動作
- `make kedro-test` → 0 tests（テスト未実装の期待通り）
