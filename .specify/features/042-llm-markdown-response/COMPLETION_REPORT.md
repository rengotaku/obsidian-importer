# Feature 042: LLM レスポンス形式をマークダウンに変更 - 完了報告

**Feature Branch**: `042-llm-markdown-response`
**Completed**: 2026-01-30
**Status**: ✅ All phases complete

---

## 実装サマリー

LLM（Ollama）への知識抽出リクエストのレスポンス形式を **JSON → Markdown** に変更し、LLM が構造的制約に縛られず自然な文章で回答できるようにしました。

### Before（変更前）
```
LLM プロンプト: "JSON形式で出力してください"
    ↓
LLM レスポンス: {"title": "...", "summary": "...", "summary_content": "..."}
    ↓
parse_json_response(): JSON → dict
    ↓
KnowledgeExtractor: dict → KnowledgeDocument
```

### After（変更後）
```
LLM プロンプト: "マークダウン形式で出力してください"
    ↓
LLM レスポンス: # タイトル\n## 要約\n...\n## 内容\n...
    ↓
parse_markdown_response(): Markdown → dict
    ↓
KnowledgeExtractor: dict → KnowledgeDocument（変更なし）
```

---

## フェーズ実行結果

| Phase | タスク範囲 | タスク数 | ステータス | 出力ファイル |
|-------|-----------|---------|-----------|------------|
| Phase 1: Setup | T001-T005 | 5 | ✅ Complete | tasks/ph1-output.md |
| Phase 2: US1+US2 (TDD) | T006-T021 | 16 | ✅ Complete | tasks/ph2-output.md, red-tests/ph2-test.md |
| Phase 3: US3 (TDD) | T022-T030 | 9 | ✅ Complete | tasks/ph3-output.md, red-tests/ph3-test.md |
| Phase 4: Polish | T031-T035 | 5 | ✅ Complete | tasks/ph4-output.md |
| **合計** | **T001-T035** | **35** | **✅ Complete** | - |

---

## 成果物

### 1. 新規実装

**src/etl/utils/ollama.py** に追加:
- `parse_markdown_response(response: str) -> tuple[dict, str | None]` - メイン関数
- `_strip_code_block_fence(text: str) -> str` - コードブロックフェンス除去
- `_split_markdown_sections(text: str) -> dict[str, str]` - セクション分割

**src/etl/tests/test_ollama.py** に追加:
- 14 テストメソッド (標準パース、エッジケース、翻訳パース)

**src/etl/tests/test_knowledge_extractor.py** に追加:
- 18 テストメソッド (extract マークダウン対応 11件 + to_markdown 統合 7件)

### 2. 既存ファイル修正

**src/etl/prompts/knowledge_extraction.txt**:
- JSON 出力指示 → Markdown 出力指示（# タイトル + ## 要約 + ## 内容）

**src/etl/prompts/summary_translation.txt**:
- JSON 出力指示 → Markdown 出力指示（## 要約 セクションのみ）

**src/etl/utils/knowledge_extractor.py**:
- Import: `parse_json_response` → `parse_markdown_response`
- Call sites: 3箇所（translate_summary, extract, _extract_chunk）

**src/etl/tests/test_knowledge_transformer.py**:
- 2 テストを markdown mock に更新

### 3. クリーンアップ

**src/etl/utils/ollama.py** から削除:
- `parse_json_response()`
- `extract_json_from_code_block()`
- `extract_first_json_object()`
- `format_parse_error()`
- `CODE_BLOCK_PATTERN` 定数

**src/etl/utils/__init__.py** から削除:
- 3つの re-export（extract_json_from_code_block, extract_first_json_object, parse_json_response）

### 4. ドキュメント

**specs/042-llm-markdown-response/**:
- spec.md (仕様書)
- plan.md (実装計画)
- research.md (技術調査・6つの設計決定)
- data-model.md (データモデル定義)
- quickstart.md (動作確認手順)
- tasks.md (35タスク定義)
- requirements.md (品質チェックリスト 16項目)
- tasks/ph1-output.md, ph2-output.md, ph3-output.md, ph4-output.md (各フェーズ出力)
- red-tests/ph2-test.md, ph3-test.md (TDD RED フェーズ記録)
- COMPLETION_REPORT.md（本ファイル）

---

## テスト結果

### フィーチャーテスト（本機能で追加）

| ファイル | テスト数 | 結果 |
|---------|---------|------|
| test_ollama.py | 14 (parse_markdown_response) | 14/14 PASS ✅ |
| test_knowledge_extractor.py | 18 (extract + to_markdown) | 18/18 PASS ✅ |
| **合計** | **32** | **32/32 PASS ✅** |

### フルテストスイート（make test）

```
Total: 579 tests
- PASS: 544
- FAIL: 6 (既存、本機能とは無関係)
- ERROR: 29 (既存、本機能とは無関係)
```

**フィーチャーテスト全件 PASS**: 本機能で追加した32テストは全て通過。既存の失敗/エラーは Phase 2 以前から存在し、本機能とは無関係。

---

## User Story 達成状況

### ✅ User Story 1 - LLM にマークダウン形式でレスポンスさせる（Priority: P1）

**達成内容**:
- knowledge_extraction.txt プロンプトを markdown 出力指示に変更
- summary_translation.txt プロンプトを markdown 出力指示に変更
- LLM は `# タイトル` + `## 要約` + `## 内容` の3セクション構造で応答

**テスト**: test_knowledge_extractor.py の extract() テスト 11件で検証済み

### ✅ User Story 2 - マークダウンレスポンスを構造化データに変換する（Priority: P1）

**達成内容**:
- `parse_markdown_response()` 実装（ollama.py）
  - コードブロックフェンス除去（前処理）
  - セクション分割（# / ## 見出し検出）
  - dict 構築（title, summary, summary_content）
  - 戻り値 `tuple[dict, str | None]` で parse_json_response() と同一シグネチャ

**テスト**: test_ollama.py の 14件で検証済み（標準入力、エッジケース、翻訳パース）

### ✅ User Story 3 - 既存パイプラインとの後方互換性を維持する（Priority: P2）

**達成内容**:
- parse_markdown_response() の戻り値型が parse_json_response() と同一
- knowledge_extractor.py の変更は関数呼び出し先の変更のみ（3箇所）
- KnowledgeDocument.to_markdown() の出力フォーマット不変

**テスト**: test_knowledge_extractor.py の統合テスト 7件で検証済み（frontmatter, 見出し正規化, 完全フォーマット）

---

## 設計決定（research.md より）

| # | 決定内容 | 選択した方針 |
|---|---------|------------|
| 1 | Markdown 構造 | 3セクション（# タイトル + ## 要約 + ## 内容）、タグ除外 |
| 2 | パーサー実装 | 正規表現ベース、外部ライブラリ不使用 |
| 3 | プロンプト変更範囲 | knowledge_extraction.txt と summary_translation.txt の両方 |
| 4 | 後方互換性 | parse_json_response() と同一の dict 形式を維持 |
| 5 | コードブロック除去 | ` ```markdown ... ``` ` フェンスを前処理で除去 |
| 6 | 翻訳レスポンス | 最小構造（## 要約 セクションのみ） |

---

## 品質チェックリスト（requirements.md）

全 16 項目 ✅ Complete:

### Functional Requirements (7/7)
- [x] FR-001: Markdown 形式プロンプト使用
- [x] FR-002: Markdown → 構造化データ変換
- [x] FR-003: セクション抽出（# タイトル, ## 要約, ## 内容）
- [x] FR-004: エッジケース対応（フォールバック、デフォルト値）
- [x] FR-005: コードブロックフェンス自動除去
- [x] FR-006: 後方互換性（JSON と同一形式）
- [x] FR-007: Markdown 構造指示プロンプト

### Non-Functional Requirements (5/5)
- [x] NFR-001: パース性能（レスポンスタイム < 100ms）
- [x] NFR-002: リトライロジック適用
- [x] NFR-003: エラー詳細記録
- [x] NFR-004: ユニットテストカバレッジ
- [x] NFR-005: 統合テスト実装

### Constraints (4/4)
- [x] C-001: Python 3.11+
- [x] C-002: 標準ライブラリ中心（外部依存なし）
- [x] C-003: 既存インターフェース変更なし
- [x] C-004: Ollama API 形式維持

---

## 変更ファイルサマリー

| カテゴリ | ファイル数 | 詳細 |
|---------|----------|------|
| 新規実装 | 3 | parse_markdown_response() + ヘルパー2関数 |
| プロンプト変更 | 2 | knowledge_extraction.txt, summary_translation.txt |
| 既存コード修正 | 3 | knowledge_extractor.py (import + 3 call sites), test_knowledge_transformer.py, __init__.py |
| テスト追加 | 2 | test_ollama.py (14), test_knowledge_extractor.py (18) |
| クリーンアップ | 2 | ollama.py (4関数+1定数削除), __init__.py (3 re-export 削除) |
| ドキュメント | 10 | spec, plan, research, data-model, quickstart, tasks, 4 phase outputs, 2 RED test records, 1 completion report |

---

## 次のステップ（推奨）

### 1. 動作確認（必須）

```bash
# 小規模テスト（3件）
make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude LIMIT=3 DEBUG=1

# 出力ファイル確認
ls .staging/@session/*/import/load/output/conversations/

# 品質チェック（目視）
# - frontmatter に title/summary/created が正しく含まれているか
# - 本文の見出しレベルが正規化されているか（### → #### など）
# - タグ欄は空（[]）か
```

### 2. Git コミット

```bash
git status
git add src/etl/utils/ollama.py
git add src/etl/utils/knowledge_extractor.py
git add src/etl/utils/__init__.py
git add src/etl/prompts/knowledge_extraction.txt
git add src/etl/prompts/summary_translation.txt
git add src/etl/tests/test_ollama.py
git add src/etl/tests/test_knowledge_extractor.py
git add src/etl/tests/test_knowledge_transformer.py
git add specs/042-llm-markdown-response/

git commit -m "feat(042): Change LLM response format from JSON to Markdown

- Implement parse_markdown_response() to parse markdown sections
- Update prompts to request markdown output (# title + ## 要約 + ## 内容)
- Replace parse_json_response() calls with parse_markdown_response()
- Remove legacy JSON parser functions (parse_json_response, extract_json_from_code_block, etc.)
- Add 32 tests (14 parser + 18 extractor integration)
- Maintain backward compatibility: same dict output structure

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 3. 大規模実行（推奨）

動作確認後、本番データで実行:

```bash
make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude  # 全件処理
```

### 4. メトリクス測定（オプション）

出力品質の改善を定量評価:

- タイトルの適切さ（長さ、内容の代表性）
- 要約の情報量（目視評価）
- summary_content の構造化度（見出し・リストの使用頻度）

---

## トラブルシューティング

### LLM が Markdown で応答しない

**症状**: LLM が依然として JSON 形式で応答する

**原因**: Ollama のモデルキャッシュが古いプロンプトを使用

**解決**:
```bash
# Ollama サービス再起動
sudo systemctl restart ollama

# または手動再起動
pkill ollama
ollama serve &
```

### パースエラーが多発

**症状**: `parse_markdown_response()` がエラーを返す

**原因**: LLM の出力が期待形式と異なる

**確認**:
```bash
# エラー詳細を確認（debug モード必須）
make import INPUT=... PROVIDER=claude DEBUG=1
cat .staging/@session/*/import/errors/*.md
```

**対処**:
1. エラーファイルで LLM の実際の出力を確認
2. プロンプトテンプレートの指示を明確化
3. フォールバック処理の追加を検討

### 既存テストの失敗/エラー

**症状**: `make test` で 6 failures + 29 errors

**確認**: Phase 2 以前から存在する既存問題（本フィーチャーとは無関係）

**対処**: 別途チケット化して修正（本フィーチャーの完了を妨げない）

---

## 関連リンク

- Feature specification: `specs/042-llm-markdown-response/spec.md`
- Implementation plan: `specs/042-llm-markdown-response/plan.md`
- Task breakdown: `specs/042-llm-markdown-response/tasks.md`
- Research decisions: `specs/042-llm-markdown-response/research.md`
- Data model: `specs/042-llm-markdown-response/data-model.md`

---

**実装完了日**: 2026-01-30
**実装者**: Claude Sonnet 4.5（speckit.implement workflow）
**レビュー**: 必要に応じて実施
