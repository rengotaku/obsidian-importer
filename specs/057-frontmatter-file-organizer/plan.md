# Implementation Plan: Frontmatter ファイル振り分けスクリプト

**Branch**: `057-frontmatter-file-organizer` | **Date**: 2026-02-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/057-frontmatter-file-organizer/spec.md`

## Summary

frontmatter の genre/topic に基づいて、ETL処理済みファイルを Obsidian Vault に振り分けるスタンドアロンスクリプトを実装する。プレビューモード（dry-run）と実行モードを提供し、Makefile 経由で実行可能にする。

## Technical Context

**Language/Version**: Python 3.11+ (既存プロジェクト準拠)
**Primary Dependencies**: PyYAML (既存依存関係)
**Storage**: ファイルシステム（Markdown ファイル）
**Testing**: unittest（標準ライブラリ、既存テストパターン準拠）
**Target Platform**: Linux/macOS（ローカル開発環境）
**Project Type**: Single project - スタンドアロンスクリプト
**Performance Goals**: 1000ファイルを5秒以内にプレビュー、1ファイル100ms以内で移動
**Constraints**: 同名ファイル衝突時はスキップ、データ損失ゼロ
**Scale/Scope**: 1000ファイル程度の処理を想定

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

このプロジェクトには constitution.md が存在しないため、CLAUDE.md の方針に従う：
- ✅ レガシーコード（src/converter/）は修正しない - 新規スクリプト作成
- ✅ シンプルさ優先 - スタンドアロンスクリプトとして実装
- ✅ 後方互換性は考慮しない - 破壊的変更可能

## Project Structure

### Documentation (this feature)

```text
specs/057-frontmatter-file-organizer/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
scripts/
└── organize_files.py    # メインスクリプト（新規作成）

conf/base/
├── genre_mapping.yml.sample  # サンプル設定（コミット）
└── genre_mapping.yml         # 実設定（gitignore）

tests/
└── test_organize_files.py    # ユニットテスト

Makefile                      # ターゲット追加
.gitignore                    # genre_mapping.yml 追加
```

**Structure Decision**: Kedro パイプラインではなく、独立した `scripts/` ディレクトリにスタンドアロンスクリプトとして配置。ETL 処理後の後処理ツールとして位置づける。

## Complexity Tracking

> 違反なし - シンプルなスタンドアロンスクリプト構成
