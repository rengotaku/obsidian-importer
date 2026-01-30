# Feature Specification: Plan Status Test

## Overview

テスト実行時に `@test` ディレクトリをターゲットとして使用し、`@plan` ディレクトリへのセッション状態が正しく格納されているか検証する機能を追加する。現在のテストはモジュール単位の動作確認のみで、実際のセッション状態ファイルへの永続化と統合動作が検証されていない。

## Problem Statement

現在のテストインフラでは以下の問題がある：

- テストが一時ディレクトリで実行され、実際の動作フローが検証されていない
- `@plan` ディレクトリへのセッション状態ファイルの永続化が検証されていない
- 本番の `@index` を使用するリスクがある

## User Scenarios & Testing

### Scenario 1: @test フォルダでのテスト実行

**Given** `@test` フォルダにテスト用 Markdown ファイルが存在する
**When** テストコマンドを実行する
**Then** `@test` フォルダ内のファイルが処理され、`@index` は影響を受けない

### Scenario 2: セッション状態の永続化検証

**Given** `@test` フォルダでセッションを開始する
**When** ファイル処理が完了する
**Then** `@plan/{session_id}/` 配下に正しい状態ファイルが作成される

### Scenario 3: 状態ファイル形式の検証

**Given** 処理済み・エラー・保留中のファイルがある状態
**When** 状態をロードする
**Then** 各状態ファイルのJSON形式が仕様通りであること

## Functional Requirements

### FR-1: @test ディレクトリの作成

- Obsidian Vault ルートに `@test` ディレクトリを作成
- `normalizer/tests/fixtures/` のファイルを `@test` にコピー
- テスト実行時は `@test` をターゲットディレクトリとして使用

### FR-2: ターゲットディレクトリ切り替え

- 環境変数 `NORMALIZER_INDEX_DIR` で `@test` を指定可能（既存機能）
- Makefile ターゲットでテスト用設定を自動適用

### FR-3: セッション状態ファイルの検証

以下のファイルが正しく作成・更新されることを検証：

1. **session.json** - セッションメタデータ
2. **pending.json** - 未処理ファイルリスト
3. **processed.json** - 処理済みファイルリスト
4. **errors.json** - エラーファイルリスト

### FR-4: 統合テストの追加

- `@test` → `@plan` の一連のフローをテスト
- 状態ファイルの内容検証

## Success Criteria

- `@test` フォルダがテスト用ターゲットとして機能する
- セッション状態ファイルの作成・更新・読み込みが検証できる
- 本番の `@index` に影響を与えない

## Assumptions

- `@test` ディレクトリは Obsidian Vault ルートに作成
- 既存の `NORMALIZER_INDEX_DIR` 環境変数機能を活用
- 統合テストは既存テストファイルに追加

## Scope

### In Scope

- `@test` ディレクトリの作成とフィクスチャ配置
- Makefile での `@test` ターゲット設定
- セッション状態の統合テスト

### Out of Scope

- `@test` フォルダの自動クリーンアップ
- 並行セッションのテスト
- パフォーマンステスト
