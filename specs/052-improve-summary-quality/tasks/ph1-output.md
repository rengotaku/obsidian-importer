# Phase 1 Output: Setup

**Date**: 2026-02-16
**Status**: Complete

## T001: Current Prompt Analysis

**File**: `src/obsidian_etl/utils/prompts/knowledge_extraction.txt`

Current prompt structure:
- タスク定義
- 出力形式（Markdown テンプレート）
- 抽出ルール（タイトル、要約、タグ、内容）
- 形式選択基準（表、リスト、小見出し）
- コードの扱い
- 禁止事項
- 情報量の目安（サイズ別最小出力量）
- 省略禁止ルール
- 品質基準
- NG例

**現状の問題点**:
- 「理由・背景」の説明指示がない
- 表形式データの保持指示が弱い
- 分析・推奨の構造化指示がない

## T002: extract_knowledge Node

**File**: `src/obsidian_etl/pipelines/transform/nodes.py`

Functions:
- `extract_knowledge`: LLM による知識抽出
- `generate_metadata`: メタデータ生成
- `format_markdown`: Markdown 出力フォーマット

compression_validator を使用して圧縮率を検証済み。

## T003: Existing Tests

**File**: `tests/pipelines/transform/test_nodes.py`

Test classes (14):
- TestExtractKnowledge
- TestExtractKnowledgeEnglishSummaryTranslation
- TestExtractKnowledgeErrorHandling
- TestGenerateMetadata
- TestFormatMarkdown
- TestFormatMarkdownOutputFilename
- TestIdempotentTransform
- TestExtractKnowledgeEmptyContent
- TestSanitizeFilename
- TestExtractKnowledgeReviewReason
- TestFormatMarkdownReviewOutput
- TestExtractKnowledgeSummaryLength
- TestExtractKnowledgeUsesOllamaConfig
- TestTranslateSummaryUsesOllamaConfig

## T004-T005: Golden File Candidates

**organized/** (264 files):
- 技術系多数: Claude, AWS, Docker, Python 等
- ビジネス系: 旅行、赤ちゃん関連
- 日常系: 3Dプリンター、Bluetooth 等

**review/** (94 files):
- 大きなファイルが多い（10KB-50KB）
- 圧縮率が低いファイル

### 選定候補

| カテゴリ | サイズ | ファイル | ソース |
|---------|--------|---------|--------|
| 技術系・小 | <2KB | Automatic1111 positive prompt 設定.md | organized |
| 技術系・中 | 2-5KB | API GatewayとLoad Balancerの違い.md | organized |
| 技術系・大 | >5KB | Claude CLI 設定確認問題.md | review |
| ビジネス系・小 | <2KB | 8ヶ月の赤ちゃん飛行機搭乗時の睡眠対策.md | organized |
| ビジネス系・中 | 2-5KB | 9ヶ月の赤ちゃんとの飛行機搭乗のコツ.md | organized |
| 日常系・小 | <2KB | 3Dプリンターでオリジナルグッズを作る.md | organized |
| 表形式・中 | 2-5KB | (要確認) | review |
| 表形式・大 | >5KB | 千葉のSwitch2販売実績.md | review |
| コード含む・小 | <2KB | Bash Alias 設定トラブルシューティング.md | organized |
| コード含む・中 | 2-5KB | AWS Skill Builder レッスンのテキスト取得方法.md | organized |

## Next Phase

Phase 2 (User Story 1 - MVP) に進む準備完了。
- プロンプト改善タスク (T008-T016)
- TDD フロー: tdd-generator → phase-executor
