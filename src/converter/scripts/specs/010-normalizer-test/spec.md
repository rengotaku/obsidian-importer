# Feature Specification: Normalizer Test Infrastructure

## Overview

ollama_normalizer.py（現 normalizer パッケージ）の主要機能をテストするためのテストインフラを実装する。`@index` フォルダの代わりに `@test` フォルダを使用して、本番データに影響を与えずにテストを実行できるようにする。

## Problem Statement

現在、normalizer の動作確認は手動で `@index` フォルダを使用して行っている。これには以下の問題がある：

- 本番データが影響を受けるリスク
- 再現性のあるテストができない
- CI/CD 統合が困難

## User Scenarios & Testing

### Scenario 1: テスト実行

**Given** テスト用の Markdown ファイルが `@test` フォルダに存在する
**When** テストコマンドを実行する
**Then** `@test` フォルダ内のファイルで処理が行われ、`@index` は影響を受けない

### Scenario 2: テストフィクスチャ使用

**Given** 様々な形式の Markdown ファイル（frontmatter あり/なし、英語/日本語）
**When** 各テストケースを実行する
**Then** 期待される正規化結果が得られる

## Functional Requirements

### FR-1: テストディレクトリ切り替え

- `@test` フォルダをテスト用の入力ディレクトリとして使用可能
- コマンドラインオプションまたは環境変数で切り替え
- `@index` フォルダは通常運用時のみ使用

### FR-2: 主要機能のテスト

以下の主要機能のテストを実装：

1. **ファイル読み込み・書き込み** (io/files.py)
2. **frontmatter 解析・生成** (validators/)
3. **ジャンル分類** (pipeline/stages.py の classify)
4. **英語文書検出** (detection/english.py)
5. **セッション管理** (state/manager.py, io/session.py)

### FR-3: テストフィクスチャ

- テスト用の Markdown ファイルを `tests/fixtures/` に配置
- 様々なパターンのファイルを用意（正常系・異常系）

## Success Criteria

- テストコマンド一発で全テストが実行できる
- 本番の `@index` フォルダが影響を受けない
- 主要機能の動作が検証できる

## Assumptions

- Python 標準ライブラリの unittest を使用
- Ollama API は実際に呼び出さずモック化
- テスト用の `@test` フォルダは空の状態から開始可能

## Scope

### In Scope

- 主要機能のユニットテスト
- テストディレクトリ切り替え機能
- テストフィクスチャ整備

### Out of Scope

- 網羅的なテスト（主要機能のみ）
- パフォーマンステスト
- E2E テスト
