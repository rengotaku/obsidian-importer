# Phase 2 Output

## 作業概要
- Phase 2 (US1 + US2) - マークダウンパーサー実装 & プロンプト変更の GREEN 実装完了
- FAIL テスト 36 件 (test_ollama: 25, test_knowledge_extractor: 11) を全て PASS させた
- 既存テスト test_knowledge_transformer.py の 2 件を markdown 形式に更新

## 修正ファイル一覧
- `src/etl/utils/ollama.py` - `parse_markdown_response()` 関数と内部ヘルパー (`_strip_code_block_fence`, `_split_markdown_sections`) を追加
- `src/etl/prompts/knowledge_extraction.txt` - JSON 出力指示をマークダウン出力指示に変更 (`# タイトル` + `## 要約` + `## 内容`)
- `src/etl/prompts/summary_translation.txt` - JSON 出力指示をマークダウン出力指示に変更 (`## 要約` セクションのみ)
- `src/etl/utils/knowledge_extractor.py` - `parse_json_response` を `parse_markdown_response` に置換 (import + 3 call sites)
- `src/etl/tests/test_knowledge_transformer.py` - 既存テスト 2 件を markdown mock レスポンスに更新

## 注意点
- `parse_json_response()` とその関連関数 (`extract_json_from_code_block`, `extract_first_json_object`, `format_parse_error`) は ollama.py に残存。Phase 4 (Polish) で整理予定
- `_extract_chunk()` メソッド内の `parse_json_response` も `parse_markdown_response` に置換済み
- 既存テストの failures 6 件 + errors 29 件は本 Phase 以前から存在するもの（CLI, stages, session, debug_step 等）

## 実装のミス・課題
- 初回実装で `## 内容` セクション内のサブ見出し（`### 基本構文` 等）を新セクションとして扱ってしまい、内容が分断される問題が発生。`level >= 3` かつ `current_section == "content"` の場合はセクション分割せず content に含めるよう修正
- `test_knowledge_transformer.py` の既存テストが JSON mock を使用していたため、markdown mock に更新が必要だった
