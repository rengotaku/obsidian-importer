# Quickstart: Summary品質改善

## 概要

**目的**: Claude会話ログのSummaryを「会話経緯説明」から「知識抽出型の構造化された要約」に変換

**アプローチ**: 新規 Stage 5 (`stage5_summary`) をパイプラインに追加

**主要変更点**:
- `stage5_summary.txt` プロンプト新規作成
- `stages.py` に stage5_summary() 関数追加
- `runner.py` で stage4 後に stage5 呼び出し

**期待する出力**:
- 日本語会話 → 日本語Summary
- 箇条書き/構造化形式、500文字以内
- 「User asked」「Claude said」等の会話経緯表現を排除

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `prompts/stage5_summary.txt` | 新規作成 |
| `normalizer/config.py` | STAGE_PROMPTS追加 |
| `normalizer/models.py` | Stage5Result追加 |
| `normalizer/pipeline/stages.py` | stage5_summary()追加 |
| `normalizer/pipeline/runner.py` | stage5呼び出し追加 |

## 1. プロンプト作成

`prompts/stage5_summary.txt`:

```text
あなたはナレッジベースキュレーターです。
Summaryセクションを「会話経緯の説明」から「知識抽出型の構造化された要約」に改善してください。

## 入力
Summaryセクションを含むMarkdownコンテンツが与えられます。

## 改善ルール

### 言語
- 日本語の会話 → 日本語でSummary
- 英語の会話 → 英語でSummary

### 形式
- 箇条書きまたは構造化された形式で核心情報を提示
- 500文字以内、3-5項目程度
- 最も重要な知識・結論を抽出

### 禁止事項（重要）
以下の表現は絶対に使用しないでください：
- "The user asked", "Claude provided", "Claude said"
- "ユーザーが質問した", "Claudeが回答した"
- 会話の流れや経緯の説明

### Good Example
## Summary

2024-2025年のCSSデファクトスタンダード:

- **主流**: Tailwind CSS + モダンCSS
- **CSS-in-JS**: styled-components → Panda CSS へ移行傾向
- **プリプロセッサ**: Sass/SCSS は必要性低下

### Bad Example（これは避ける）
## Summary

The user asked about current CSS de facto standards. Claude provided a comprehensive overview...

## 出力形式
```json
{
  "improved_summary": "## Summary\n\n改善されたSummary内容...",
  "changes_made": ["会話経緯表現を削除", "箇条書き形式に変換"]
}
```
```

## 2. config.py 変更

```python
STAGE_PROMPTS = {
    "stage1_dust": PROMPTS_DIR / "stage1_dust.txt",
    "stage2_genre": PROMPTS_DIR / "stage2_genre.txt",
    "stage3_normalize": PROMPTS_DIR / "stage3_normalize.txt",
    "stage4_metadata": PROMPTS_DIR / "stage4_metadata.txt",
    "stage5_summary": PROMPTS_DIR / "stage5_summary.txt",  # 追加
}
```

## 3. models.py 変更

```python
class Stage5Result(TypedDict):
    improved_summary: str
    changes_made: list[str]
```

## 4. stages.py 変更

```python
def stage5_summary(normalized_content: str, filename: str, is_english: bool) -> StageResult:
    """
    Stage 5 - Summary品質改善

    Summaryセクションを知識抽出型に変換
    """
    # Summaryセクション抽出
    # LLM呼び出し
    # normalized_content更新
    # StageResult返却
```

## 5. runner.py 変更

```python
# stage4の後に追加
if stage4_result and stage4_result.success:
    stage5_result = stage5_summary(
        stage3_result.data.normalized_content,
        filename,
        pre_result.is_english_doc
    )
```

## 動作確認

```bash
# テスト実行
cd .claude/scripts && python -m pytest normalizer/tests/ -v

# 単一ファイルでの動作確認
python -m normalizer --dry-run "@index/テストファイル.md"
```

## 関連ファイル

- `specs/012-summary-quality/spec.md` - 機能仕様
- `specs/012-summary-quality/research.md` - 調査結果
