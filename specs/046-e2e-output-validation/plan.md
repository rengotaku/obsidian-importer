# Implementation Plan: E2Eテスト出力検証

**Branch**: `046-e2e-output-validation` | **Date**: 2026-02-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/046-e2e-output-validation/spec.md`

## Summary

E2Eテストの出力検証を改善する。現在は「ファイルが存在するか」のみの判定であるのを、パイプライン最終出力（`format_markdown` の Markdown）をゴールデンファイルと比較し、`difflib.SequenceMatcher` ベースの類似度90%以上で成功判定する方式に変更する。中間ステージの個別チェックは削除し、ユニットテストに委ねる。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: 標準ライブラリのみ (`difflib`, `yaml`, `unittest`)、Kedro 1.1.1
**Storage**: ファイルシステム（Markdown, JSON）
**Testing**: unittest（標準ライブラリ）、Makefile ターゲット
**Target Platform**: Linux (local development)
**Project Type**: single
**Performance Goals**: N/A（テスト実行、パフォーマンス要件なし）
**Constraints**: 外部依存追加なし（標準ライブラリ中心のプロジェクト方針）
**Scale/Scope**: テストフィクスチャ3件の会話 → 3件の Markdown ファイルを比較

## Constitution Check

*GATE: No constitution file exists. Proceeding without gate checks.*

## Project Structure

### Documentation (this feature)

```text
specs/046-e2e-output-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
tests/
├── fixtures/
│   ├── claude_test.zip          # 既存: テスト入力フィクスチャ
│   ├── openai_test.zip          # 既存: OpenAI テスト入力
│   └── golden/                  # 新規: ゴールデンファイル（Markdown）
│       ├── <file1>.md
│       ├── <file2>.md
│       └── <file3>.md
├── e2e/                         # 新規: E2E比較ロジック
│   ├── __init__.py
│   └── golden_comparator.py     # 類似度比較スクリプト
├── pipelines/                   # 既存: ユニットテスト
│   ├── extract_claude/test_nodes.py
│   ├── extract_openai/test_nodes.py
│   ├── transform/test_nodes.py
│   └── organize/test_nodes.py
└── ...

Makefile                         # 改修: test-e2e, test-e2e-update-golden
conf/test/catalog.yml            # 既存: テスト環境カタログ
```

**Structure Decision**: 既存のテストディレクトリ構成を活用。ゴールデンファイルは `tests/fixtures/golden/` に、比較ロジックは `tests/e2e/golden_comparator.py` に配置。

## Implementation Phases

### Phase 1: ゴールデンファイル比較ロジック (FR-002, FR-003, FR-004)

`tests/e2e/golden_comparator.py` を作成。

**入力**: 2つのディレクトリパス（実行出力、ゴールデンファイル）
**出力**: 比較結果（ファイルごとのスコア、成功/失敗判定）

機能:
1. Markdown をfrontmatter と body に分離する関数
2. frontmatter の類似度計算（キー存在チェック + 値の類似度）
3. body の類似度計算（`difflib.SequenceMatcher`）
4. 総合スコア計算（frontmatter × 0.3 + body × 0.7）
5. 閾値判定と結果レポート出力
6. CLI エントリポイント（Makefile から呼び出し可能）

**CLI インターフェース**:
```bash
python -m tests.e2e.golden_comparator \
  --actual data/test/07_model_output/notes \
  --golden tests/fixtures/golden \
  --threshold 0.9
```

### Phase 2: Makefile 改修 (FR-001, FR-005, FR-007, FR-008)

`test-e2e` ターゲットを改修:
1. Ollama チェック（既存維持）
2. テストデータ準備（既存維持）
3. パイプラインを `format_markdown` まで一括実行（中間チェック削除）
4. ゴールデンファイル存在チェック（FR-007）
5. 比較スクリプト呼び出し（Phase 1 のスクリプト）
6. クリーンアップ

`test-e2e-update-golden` ターゲットを新規追加:
1. Ollama チェック
2. テストデータ準備
3. パイプラインを `format_markdown` まで一括実行
4. 出力を `tests/fixtures/golden/` にコピー
5. クリーンアップ

### Phase 3: ゴールデンファイル初回生成

`make test-e2e-update-golden` を実行して初回ゴールデンファイルを生成し、リポジトリにコミットする。

## Testing Strategy

| レベル | 対象 | 検証内容 |
|--------|------|---------|
| ユニットテスト | `golden_comparator.py` | frontmatter 分離、類似度計算、閾値判定 |
| ユニットテスト | 既存ノードテスト | 出力非空、必須キー存在（既存でカバー済み） |
| E2Eテスト | `make test-e2e` | パイプライン全体 → ゴールデンファイル比較 |

### golden_comparator のユニットテスト

`tests/e2e/test_golden_comparator.py`:
- 完全一致の2ファイル → スコア 1.0
- 微差のある2ファイル → スコア 0.9〜1.0
- 大きく異なる2ファイル → スコア < 0.9
- frontmatter キー欠落 → スコア低下
- ファイル数不一致 → エラー
- ゴールデンファイル不在 → エラーメッセージ

## Risk & Mitigation

| リスク | 影響 | 対策 |
|--------|------|------|
| LLM出力の揺れが90%閾値を超える | テストが不安定になる | 閾値をパラメータ化し調整可能にする |
| Ollamaモデル更新後にテスト全失敗 | CI/CDブロック | `make test-e2e-update-golden` で即座に再生成 |
| ゴールデンファイルのコミット忘れ | テスト実行不可 | FR-007 のエラーメッセージで案内 |
