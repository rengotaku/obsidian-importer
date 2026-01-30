# Feature Specification: Scripts コードリファクタリング

**Feature Branch**: `009-scripts-refactor`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: ".claude/scripts のコードをリファクタリング。主にはモジュール分割しAIが処理しやすい単位のコード量にする。"

## 背景と目的

`.claude/scripts/ollama_normalizer.py` は 3,233行（約112KB）の巨大なモノリシックファイルとなっており、以下の問題が発生している：

- AI（Claude等）が一度に読み込み・理解できる限界を超えている
- 変更時の影響範囲が把握しづらい
- テストの単位が大きすぎる
- 機能追加時に適切な場所を見つけにくい

本リファクタリングは、コードを論理的なモジュールに分割し、各モジュールを300-500行程度の扱いやすいサイズに保つことを目的とする。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 開発者がコードを修正する (Priority: P1)

開発者（またはAI）が特定の機能を修正・拡張する際に、関連するコードを素早く特定し、影響範囲を限定して変更できる。

**Why this priority**: リファクタリングの主目的であり、日常的な開発作業の効率に直結する。

**Independent Test**: 特定の機能（例：タグ検証）を修正する際、1つのモジュールファイルのみを読み込めば変更が完結することを確認する。

**Acceptance Scenarios**:

1. **Given** 分割されたコードベース, **When** タグ検証ロジックを修正したい, **Then** `validators/tags.py` のみを読み込んで修正が完結する
2. **Given** 分割されたコードベース, **When** LLMパイプラインのステージを追加したい, **Then** `pipeline/` ディレクトリ内の関連ファイルのみで変更が完結する
3. **Given** 分割されたコードベース, **When** 新しいファイル操作機能を追加したい, **Then** `io/` ディレクトリに新規モジュールを追加するだけで実装できる

---

### User Story 2 - 既存機能が正常に動作し続ける (Priority: P1)

リファクタリング後も、既存の全機能（ファイル正規化、ジャンル分類、dust判定など）が同じ入出力で動作する。

**Why this priority**: 機能の後退は許容できないため、P1と同等の優先度。

**Independent Test**: 既存のテストフィクスチャを使用し、リファクタリング前後で同一の出力が得られることを確認する。

**Acceptance Scenarios**:

1. **Given** リファクタリング後のコード, **When** `make test-fixtures` を実行, **Then** 全テストケースがリファクタリング前と同じ結果を返す
2. **Given** リファクタリング後のコード, **When** `--all --preview` で@index処理を実行, **Then** 分類結果がリファクタリング前と一致する
3. **Given** リファクタリング後のコード, **When** コマンドラインオプションを使用, **Then** 全オプションが同じ動作をする

---

### User Story 3 - AIが効率的にコードを理解する (Priority: P2)

Claude等のAIがコードベースを探索する際、各モジュールが300-500行以内に収まり、一度の読み込みで機能を完全に把握できる。

**Why this priority**: リファクタリングの主要な動機だが、US1/US2が前提条件。

**Independent Test**: 各分割モジュールの行数を計測し、目標範囲内であることを確認する。

**Acceptance Scenarios**:

1. **Given** 分割されたモジュール群, **When** 任意のモジュールファイルを選択, **Then** 行数が500行以下である
2. **Given** 分割されたモジュール群, **When** モジュールの依存関係を確認, **Then** 循環依存が存在しない
3. **Given** 分割されたモジュール群, **When** モジュール名を確認, **Then** 内容を推測できる命名になっている

---

### User Story 4 - エントリポイントの互換性維持 (Priority: P2)

既存の `ollama_normalizer.py` をエントリポイントとして使用し続けられ、既存のスクリプトやMakefileを変更する必要がない。

**Why this priority**: 移行コストを最小化するために重要。

**Independent Test**: 既存のMakefileターゲットがそのまま動作することを確認する。

**Acceptance Scenarios**:

1. **Given** リファクタリング後, **When** `make preview` を実行, **Then** 正常に動作する
2. **Given** リファクタリング後, **When** `python3 ollama_normalizer.py --help` を実行, **Then** 同じヘルプが表示される
3. **Given** リファクタリング後, **When** 既存のCLI引数を使用, **Then** 全て同じ動作をする

---

### Edge Cases

- 分割したモジュール間で循環インポートが発生した場合はどう対処するか？
- 既存のバックアップファイル（`.backup`）はどう扱うか？
- グローバル変数（`_current_session_dir` 等）の状態管理はどのモジュールが責任を持つか？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `ollama_normalizer.py` を複数のモジュールファイルに分割しなければならない
- **FR-002**: 各モジュールファイルは500行以下でなければならない
- **FR-003**: システムは既存の全コマンドラインオプションを同じ動作で提供し続けなければならない
- **FR-004**: システムは既存のテストフィクスチャで同じ出力を生成しなければならない
- **FR-005**: 分割されたモジュール間に循環依存があってはならない
- **FR-006**: `ollama_normalizer.py` は引き続きメインエントリポイントとして機能しなければならない
- **FR-007**: 各モジュールは単一責任の原則に従い、明確な役割を持たなければならない
- **FR-008**: 共通の型定義は専用モジュールに集約しなければならない

### モジュール分割案

現在のコード構造分析に基づく分割案：

| モジュール | 責任 | 推定行数 |
|-----------|------|---------|
| `config.py` | 設定値、定数、パス定義 | ~100 |
| `types.py` | TypedDict、型定義 | ~100 |
| `validators/title.py` | タイトル検証 | ~80 |
| `validators/tags.py` | タグ検証・正規化 | ~150 |
| `validators/format.py` | Markdownフォーマット検証 | ~100 |
| `detection/english.py` | 英語文書判定 | ~100 |
| `pipeline/stages.py` | LLMパイプラインステージ | ~400 |
| `pipeline/runner.py` | パイプライン実行 | ~200 |
| `io/files.py` | ファイル読み書き | ~150 |
| `io/session.py` | セッション管理 | ~150 |
| `state/manager.py` | 状態管理 | ~150 |
| `processing/single.py` | 単一ファイル処理 | ~200 |
| `processing/batch.py` | バッチ処理 | ~150 |
| `output/formatters.py` | 出力フォーマット | ~150 |
| `output/diff.py` | 差分表示 | ~100 |
| `cli/parser.py` | CLIパーサー | ~150 |
| `cli/commands.py` | CLIコマンド実装 | ~300 |
| `ollama_normalizer.py` | エントリポイント | ~50 |

### Key Entities

- **Module**: 分割されたPythonファイル、単一の責任を持つ
- **Pipeline Stage**: LLM処理の各段階（dust判定、ジャンル分類、正規化、メタデータ生成）
- **Session**: 処理の実行単位、状態を保持
- **Processing State**: ファイル処理の進捗状態

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 全モジュールファイルが500行以下である
- **SC-002**: 既存テストフィクスチャの全ケースで出力が一致する（100%互換性）
- **SC-003**: 循環依存が0件である
- **SC-004**: 既存CLIオプションが100%動作する
- **SC-005**: メインエントリポイント（`ollama_normalizer.py`）が100行以下である
- **SC-006**: 各モジュールが単一の明確な責任を持つ（モジュール名から役割が推測可能）

## Assumptions

- リファクタリングは機能追加を含まない（純粋なコード再構成）
- 既存のバックアップファイル（`.backup`）は削除可能
- Python 3.11+の標準ライブラリのみを使用する制約は維持
- ディレクトリ構造は `.claude/scripts/normalizer/` 配下に新規作成
