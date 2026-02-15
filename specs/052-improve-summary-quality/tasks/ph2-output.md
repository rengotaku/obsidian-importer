# Phase 2 Output

## 作業概要
- Phase 2 - User Story 1 (まとめ品質の向上) の実装完了
- FAIL テスト 10 件を PASS させた
- プロンプト改善により、理由説明、表形式保持、コードブロック保持を強化
- 短い会話への圧縮率しきい値緩和を実装

## 修正ファイル一覧

### 1. `src/obsidian_etl/utils/prompts/knowledge_extraction.txt`
- **変更内容**: V2 qualitative instructions を追加
- **追加セクション**:
  - `## 分析・考察の記述`: 理由・背景、パターン・傾向、推奨・アドバイスの記述を要求
  - `## 表形式データの保持`: Markdown 表形式での保持、数値・日付の省略禁止
  - `## コード主体の会話`: 重要なコードの完全保持、コードブロック保持優先

### 2. `src/obsidian_etl/utils/compression_validator.py`
- **変更内容**: 新規関数 `min_output_chars()` を追加、`get_threshold()` を拡張
- **追加機能**:
  - `min_output_chars(original_size: int) -> int`: 最小出力文字数を計算 (max(original*0.2, 300))
  - `get_threshold()` の拡張: < 1000 文字の会話で 30% しきい値に緩和 (従来は 20%)
- **既存動作への影響**:
  - 10,000+ 文字: 10% (変更なし)
  - 5,000-9,999 文字: 15% (変更なし)
  - 1,000-4,999 文字: 20% (変更なし)
  - < 1,000 文字: 30% (新規、緩和)

### 3. `tests/utils/test_compression_validator.py`
- **変更内容**: 既存テスト `test_get_threshold_small` を更新
- **理由**: 新しい仕様 (< 1000 文字で 30% しきい値) に対応

## テスト結果

```
Ran 341 tests in 8.454s

OK
```

- **全テスト PASS**: 341 件
- **新規テスト**: 10 件 (Phase 2 で追加)
- **回帰テストなし**: 既存テスト全て PASS

## Phase 2 完了時の仕様

### FR-001: 理由・背景の説明
- プロンプトに「理由・背景: なぜそうなるかを必ず説明」を追加
- テスト: `test_prompt_includes_reason_instruction` PASS

### FR-002: 最小出力量の保証
- `min_output_chars()` 関数を実装: max(original_size * 0.2, 300)
- テスト: `test_min_output_chars_*` 4 件すべて PASS

### FR-003: 表形式データの保持
- プロンプトに「必ず Markdown 表形式で保持」「数値・日付は省略せず」を追加
- テスト: `test_prompt_includes_table_preservation` PASS

### FR-004: 数値・日付の省略禁止
- プロンプトに「数値・日付は省略せず記載」を明記
- テスト: `test_prompt_includes_specific_values_preservation` PASS

### FR-005: 分析・考察の構造化
- プロンプトに「分析・考察の記述」セクションを追加
- テスト: `test_prompt_includes_analysis_structuring` PASS

### Edge Case: 短い会話のしきい値緩和
- < 1000 文字の会話で 30% しきい値に緩和
- テスト: `test_get_threshold_very_short_relaxed` PASS

### Edge Case: コードブロック保持の強化
- プロンプトに「コード主体の会話」セクションを追加
- テスト: `test_prompt_includes_code_preservation` PASS

## 注意点

### 次 Phase (Phase 3) で必要な情報
- ゴールデンファイルの選定時、以下の要件を満たすファイルを選択すること:
  - 表形式データを含むファイル (千葉のSwitch2販売実績.md 推奨)
  - コードブロックを含むファイル (技術系)
  - 短い会話 (< 1000 文字) のファイル
  - 分析・考察を含むファイル (ビジネス系、経済系)

### プロンプト修正のポイント
- 既存の「品質基準」セクションの直前に新規セクション 3 つを挿入
- 既存の構造・記述スタイルを維持

## 実装のミス・課題

なし。全テスト PASS、回帰なし。

## Phase 2 完了チェックリスト

- [x] RED テスト 10 件をすべて PASS
- [x] `make test` で全テスト (341 件) PASS
- [x] プロンプトに V2 qualitative instructions を追加
- [x] 圧縮率検証ロジックを拡張 (min_output_chars, 短い会話のしきい値緩和)
- [x] tasks.md を更新 (T012-T016 を [x] に)
- [x] ph2-output.md を生成

**ステータス**: Complete
