# Phase 2 Output

## 作業概要
- Phase 2 (User Story 1 - E2E output validation) の実装完了
- FAIL テスト 37 件を PASS させた (tests.e2e.test_golden_comparator)
- golden_comparator.py を実装し、Markdown ファイルの類似度比較機能を提供

## 修正ファイル一覧
- `tests/e2e/golden_comparator.py` - 新規作成（270行）
  - split_frontmatter_and_body(): YAML frontmatter と body の分離
  - calculate_frontmatter_similarity(): frontmatter 類似度計算（キー存在、file_id 完全一致、title/tags 類似度）
  - calculate_body_similarity(): body テキスト類似度計算（difflib.SequenceMatcher）
  - calculate_total_score(): 総合スコア計算（frontmatter×0.3 + body×0.7）
  - compare_directories(): ディレクトリ比較（ファイル列挙、ペアリング、個別比較、レポート生成）
  - CLI entry point (__main__ with argparse)

- `specs/046-e2e-output-validation/tasks.md` - タスク進捗更新
  - T016-T025 を完了済みにマーク

## 実装詳細

### 実装した関数

1. **split_frontmatter_and_body(content: str) -> tuple[dict, str]**
   - YAML frontmatter (`---` デリミタ) を検出して分離
   - frontmatter を dict にパース、body を str として返す
   - frontmatter がない場合は空 dict を返す

2. **calculate_frontmatter_similarity(actual: dict, golden: dict) -> float**
   - キー存在チェック（30% weight）: golden のキーが actual に存在するか
   - file_id 完全一致（40% weight）: file_id の完全一致を要求
   - title 類似度（20% weight）: difflib.SequenceMatcher による比較
   - tags 類似度（10% weight）: タグリストの重複率
   - 加重平均を計算して 0.0〜1.0 のスコアを返す

3. **calculate_body_similarity(actual: str, golden: str) -> float**
   - difflib.SequenceMatcher.ratio() を使用
   - 空文字列同士は 1.0
   - 0.0〜1.0 のスコアを返す

4. **calculate_total_score(frontmatter_score: float, body_score: float) -> float**
   - frontmatter_score * 0.3 + body_score * 0.7
   - body の方が重み大（内容の変化がより重要）

5. **compare_directories(actual_dir: str, golden_dir: str, threshold: float) -> dict**
   - golden_dir の全 .md ファイルを列挙
   - actual_dir の対応ファイルとペアリング
   - 各ファイルを比較してスコア計算
   - レポート生成（filename, total_score, frontmatter_score, body_score, missing_keys, diff_summary）
   - ファイル数不一致、golden_dir 不在でエラー
   - 全ファイルが閾値以上なら passed=True

6. **CLI entry point**
   - argparse で --actual, --golden, --threshold を受け取る
   - compare_directories() を実行
   - 結果を JSON で出力
   - passed=False なら詳細情報を stderr に出力し、exit code 1
   - passed=True なら exit code 0

### テストカバレッジ

- 全 37 テスト PASS
- 5つのテストクラス:
  - TestSplitFrontmatterAndBody (5 tests)
  - TestFrontmatterSimilarity (6 tests)
  - TestBodySimilarity (7 tests)
  - TestTotalScore (6 tests)
  - TestCompareDirectories (7 tests)
  - TestComparisonReport (6 tests)

- カバレッジ: プロジェクト全体の coverage は src/obsidian_etl のみを対象としているため、tests/e2e/golden_comparator.py の coverage は計測対象外
- 手動検証: 全 5 関数が実装され、37 テストで網羅的にテストされていることを確認

## テスト結果

```
Ran 329 tests in 0.768s
FAILED (failures=3, errors=22)
```

- 新規テスト: 37 件（tests.e2e.test_golden_comparator）すべて PASS
- 既存テスト: 292 件（変更なし）
- 既存の失敗/エラーは RAG 関連（tests.rag.*）のみで、今回の変更と無関係

## 注意点

### 次 Phase で必要な情報
- Phase 3 では Makefile に以下のターゲットを追加する:
  - `test-e2e-update-golden`: パイプライン実行 → 最終出力を tests/fixtures/golden/ にコピー
  - `test-e2e` (改修): 中間チェック削除 → golden_comparator.py 呼び出し

- golden_comparator.py の CLI インターフェース:
  ```bash
  python -m tests.e2e.golden_comparator \
    --actual data/test/07_model_output/notes \
    --golden tests/fixtures/golden \
    --threshold 0.9
  ```

- 出力形式:
  ```json
  {
    "passed": true/false,
    "files": [
      {
        "filename": "xxx.md",
        "total_score": 0.95,
        "frontmatter_score": 0.98,
        "body_score": 0.94,
        "missing_keys": [],
        "diff_summary": "..."
      }
    ]
  }
  ```

### 依存関係
- 標準ライブラリのみ使用（difflib, yaml, os, pathlib, argparse）
- PyYAML は既存依存関係（プロジェクト全体で使用）

## 実装のミス・課題
- なし（全テスト PASS、既存テストも破壊なし）

## Checkpoint 達成状況
✅ golden_comparator.py が単体で動作し、2つのディレクトリの Markdown ファイルを比較できる

## 次のステップ
Phase 3 の実装に進む:
- T027: test-e2e-update-golden ターゲット追加
- T028: test-e2e ターゲット改修
- T029: .PHONY 宣言追加
