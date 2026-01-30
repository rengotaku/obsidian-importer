# Implementation Plan: ローカルLLM品質向上

**Branch**: `003-llm-quality-enhancement` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-llm-quality-enhancement/spec.md`

## Summary

ローカルLLM（Ollama gpt-oss:20b）によるファイル整理処理の品質を、Claude Opusの70%同等レベルに向上させる。既存の`ollama_normalizer.py`を改善し、以下を実現する：
- プロンプトエンジニアリングによるタイトル・タグ・コンテンツ品質向上
- 既存タグ辞書の自動抽出・プロンプト注入
- ルールベース後処理によるMarkdownフォーマット正規化
- 冗長表現の簡潔化・不完全文の補完・日本語化
- 低確信度ファイルの@reviewフォルダ振り分け

## Technical Context

**Language/Version**: Python 3.11+（標準ライブラリのみ使用）
**Primary Dependencies**: なし（urllib, json, pathlib等の標準ライブラリのみ）
**Storage**: ファイルシステム（Markdownファイル、JSONセッション状態）
**Testing**: pytest（新規導入）+ 手動品質評価
**Target Platform**: Linux（ローカル環境）
**Project Type**: Single project（CLIツール）
**Performance Goals**: ファイルあたり30秒以内
**Constraints**: Ollama API応答時間依存、標準ライブラリのみ使用
**Scale/Scope**: @indexフォルダ内のファイル（通常10-100件/バッチ）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 状態 | 対応 |
|------|------|------|
| I. Vault Independence | ✅ Pass | ClaudedocKnowledgesへの自動振り分けは行わない |
| II. Obsidian Markdown Compliance | ✅ Pass | YAML frontmatter必須、リンク形式準拠 |
| III. Normalization First | ✅ Pass | `normalized: true`フラグ管理を維持 |
| IV. Genre-Based Organization | ✅ Pass | 既存ジャンル分類を継続使用 |
| V. Automation with Oversight | ✅ Pass | 低確信度→@reviewフォルダで人間確認 |

**Result**: All gates passed. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-llm-quality-enhancement/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface specification)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
.claude/scripts/
├── ollama_normalizer.py     # 既存スクリプト（改善対象）
├── ollama_genre_classifier.py  # 既存（参考）
├── tag_extractor.py         # 新規: タグ辞書抽出
├── markdown_normalizer.py   # 新規: ルールベース後処理
├── prompts/                 # 新規: プロンプトテンプレート
│   ├── normalizer_v2.txt    # 改善版システムプロンプト
│   └── examples/            # Few-shot例
└── tests/                   # 新規: テストスイート
    ├── test_tag_extractor.py
    ├── test_markdown_normalizer.py
    ├── test_ollama_normalizer.py
    └── fixtures/            # テスト用サンプルファイル
```

**Structure Decision**: 既存の`.claude/scripts/`ディレクトリ構造を維持しつつ、新規モジュールを追加。標準ライブラリのみ使用の制約を維持。

## Complexity Tracking

> No violations requiring justification. Constitution gates all passed.

---

## Phase 0: Research

### Research Tasks

1. **Few-shot Prompting Best Practices for Small LLMs**
   - 20Bパラメータモデルでの効果的なプロンプト設計
   - 日本語タイトル生成の最適化

2. **Existing Tag Vocabulary Analysis**
   - 現在のVaultからタグ頻度分析
   - 一貫性のあるタグ語彙リストの設計

3. **Markdown Normalization Rules**
   - Obsidian規約に準拠した正規表現パターン
   - 見出しレベル調整アルゴリズム

4. **English Document Detection Heuristics**
   - 完全な英語文書 vs 断片的メモの判別基準
   - 文書構造・長さ・完成度の閾値設定

5. **Quality Evaluation Methodology**
   - Claude Opusとの比較評価手法
   - 自動化可能な品質メトリクス

---

## Phase 1: Design Artifacts

### Outputs to Generate

1. **research.md** - 上記リサーチ結果の統合
2. **data-model.md** - エンティティ定義（ファイル、タグ辞書、処理結果）
3. **contracts/cli.md** - CLIインターフェース仕様
4. **quickstart.md** - 開発者向けクイックスタートガイド
