# Phase 4 Output

## 作業概要
- Phase 4 (Polish) - 旧 JSON パーサー関数のクリーンアップ完了
- 4 関数を `src/etl/utils/ollama.py` から削除
- 対応する `__init__.py` の re-export も削除
- test_ollama.py には旧 JSON パーサーのテストが存在しなかったため、テスト削除は不要

## 削除した関数

| 関数名 | ファイル | 理由 |
|--------|---------|------|
| `extract_json_from_code_block()` | ollama.py | `parse_json_response` 内部でのみ使用、外部呼び出しなし |
| `extract_first_json_object()` | ollama.py | `parse_json_response` 内部でのみ使用、外部呼び出しなし |
| `format_parse_error()` | ollama.py | `parse_json_response` 内部でのみ使用、外部呼び出しなし |
| `parse_json_response()` | ollama.py | `parse_markdown_response()` に置換済み、src/etl 内で呼び出しなし |
| `CODE_BLOCK_PATTERN` | ollama.py | `extract_json_from_code_block` 専用の定数 |

## 削除した re-export

| シンボル | ファイル |
|---------|---------|
| `parse_json_response` | `utils/__init__.py` |
| `extract_json_from_code_block` | `utils/__init__.py` |
| `extract_first_json_object` | `utils/__init__.py` |

## 保持した関数
- `src/converter/` 内の同名関数はレガシーコードのため変更しない（CLAUDE.md ルール準拠）

## テスト結果

### 042 関連テスト（43/43 PASS）
- test_ollama.py: 25/25 PASS（parse_markdown_response テスト）
- test_knowledge_extractor.py: 18/18 PASS（extract + translate_summary + 統合テスト）

### make test 全体結果
- 579 tests, 6 failures, 29 errors, 15 skipped
- failures/errors は全て Phase 3 以前から存在する既存の問題（本 Phase での新規 failure なし）

## 修正ファイル一覧
- `src/etl/utils/ollama.py` - 旧 JSON パーサー関数 4 つ + 定数 1 つを削除、モジュール docstring 更新
- `src/etl/utils/__init__.py` - 旧 JSON パーサー関数の re-export 3 つを削除

## 注意点
- `src/converter/` 配下のレガシーコードには同名関数が残存（意図的に保持）
- `test_ollama.py` には旧 JSON パーサーのテストが元々存在しなかった（Phase 2 で parse_markdown_response テストのみ作成済み）

## 実装のミス・課題
- なし
