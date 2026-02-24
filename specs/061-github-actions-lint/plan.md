# Implementation Plan: GitHub Actions Lint CI

**Branch**: `061-github-actions-lint` | **Date**: 2026-02-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/061-github-actions-lint/spec.md`

## Summary

PR 作成・更新時および main ブランチへの push 時に ruff と pylint による lint チェックを自動実行する GitHub Actions CI を追加する。Makefile に個別ターゲット（`ruff`, `pylint`）を作成し、ローカルと CI で同一の実行定義を使用することで結果の一致を保証する。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: ruff (既存), pylint (新規追加)
**Storage**: N/A
**Testing**: unittest (既存)
**Target Platform**: GitHub Actions (ubuntu-latest)
**Project Type**: single (Kedro pipeline)
**Performance Goals**: CI 完了 5 分以内
**Constraints**: pip キャッシュ利用、fail-fast (ローカルのみ)
**Scale/Scope**: 単一リポジトリ、開発者 1-3 名

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution ファイルが存在しないため、このゲートはスキップ。

## Project Structure

### Documentation (this feature)

```text
specs/061-github-actions-lint/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── lint.yml         # NEW: GitHub Actions workflow

Makefile                 # UPDATE: Add ruff, pylint targets

pyproject.toml           # UPDATE: Add pylint config & pin versions
```

**Structure Decision**: 既存のプロジェクト構造を維持。GitHub Actions ワークフローと既存ファイルの更新のみ。

## Complexity Tracking

N/A - 単純な CI 追加、複雑性なし

---

## Phase 0: Research

### Research Tasks

1. **GitHub Actions best practices for Python linting**
2. **pylint configuration for Kedro projects**
3. **pip cache strategy in GitHub Actions**

### Findings

#### 1. GitHub Actions Best Practices

**Decision**: `actions/setup-python` + `actions/cache` の組み合わせ

**Rationale**:
- `actions/setup-python@v5` は `cache: 'pip'` オプションを内蔵しており、別途 `actions/cache` を使う必要がない
- pyproject.toml のハッシュをキーとして使用し、依存関係変更時に自動でキャッシュ無効化

**Alternatives considered**:
- `pip-tools` による lock file 管理 → オーバーキル
- Docker コンテナでの実行 → セットアップ時間増加

#### 2. pylint Configuration

**Decision**: pyproject.toml に `[tool.pylint]` セクションを追加

**Rationale**:
- ruff 設定と同じファイルで一元管理
- 既存の ruff と競合するルールは pylint 側で無効化

**Alternatives considered**:
- `.pylintrc` ファイル → 設定ファイル分散
- `setup.cfg` → 非推奨

**Key pylint settings**:
```toml
[tool.pylint.main]
ignore = [".venv", "venv", "__pycache__", ".staging", ".specify"]
jobs = 0  # auto-detect CPU count

[tool.pylint.messages_control]
disable = [
    "C0114",  # missing-module-docstring (ruff handles)
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "W0511",  # fixme (allow TODO comments)
    "R0903",  # too-few-public-methods
]

[tool.pylint.format]
max-line-length = 100  # match ruff
```

#### 3. pip Cache Strategy

**Decision**: `actions/setup-python` の `cache: 'pip'` オプションを使用

**Rationale**:
- ビルトイン機能で追加設定不要
- pyproject.toml のハッシュを自動でキーに使用
- キャッシュミス時は自動でフォールバック

**Alternatives considered**:
- `actions/cache` を直接使用 → 冗長
- キャッシュなし → 毎回インストールで遅い

#### 4. Version Pinning Strategy

**Decision**: pyproject.toml で厳密なバージョン固定

**Current state**:
```toml
# 現状
"ruff>=0.1.0"  # 範囲指定

# 変更後
"ruff==0.8.6"  # 固定 (最新安定版を調査して決定)
"pylint==3.3.3"  # 固定 (最新安定版を調査して決定)
```

**Rationale**:
- ローカルと CI で完全同一バージョンを保証
- 予期しないバージョンアップによる CI 失敗を防止

---

## Phase 1: Design

### Workflow Design

```yaml
# .github/workflows/lint.yml
name: Lint

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -e ".[dev]"
      - run: make ruff

  pylint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -e ".[dev]"
      - run: make pylint
```

### Makefile Design

```makefile
# 個別ターゲット
ruff:
	@echo "Running ruff..."
	@$(VENV_DIR)/bin/ruff check src/obsidian_etl/
	@echo "✅ ruff passed"

pylint:
	@echo "Running pylint..."
	@$(VENV_DIR)/bin/pylint src/obsidian_etl/
	@echo "✅ pylint passed"

# 統合ターゲット (fail-fast)
lint: ruff pylint
```

### pyproject.toml Changes

```toml
[project.optional-dependencies]
dev = [
    "coverage>=7.0",
    "ruff==0.8.6",      # PINNED
    "pylint==3.3.3",    # NEW, PINNED
    "kedro-viz>=10.0",
]

[tool.pylint.main]
ignore = [".venv", "venv", "__pycache__", ".staging", ".specify", ".claude"]
jobs = 0

[tool.pylint.messages_control]
disable = ["C0114", "C0115", "C0116", "W0511", "R0903"]

[tool.pylint.format]
max-line-length = 100
```

---

## Implementation Phases

### Phase 1: Setup (Dependencies & Config)
1. pyproject.toml に pylint 追加 & バージョン固定
2. pyproject.toml に pylint 設定追加
3. ローカルで `pip install -e ".[dev]"` 実行確認

### Phase 2: Makefile Targets
1. `ruff` ターゲット作成（既存 `lint` から分離）
2. `pylint` ターゲット作成
3. `lint` ターゲット更新（ruff → pylint 順次実行）
4. ローカルで `make ruff`, `make pylint`, `make lint` 動作確認

### Phase 3: GitHub Actions Workflow
1. `.github/workflows/lint.yml` 作成
2. ruff ジョブ定義
3. pylint ジョブ定義
4. PR 作成して CI 動作確認

### Phase 4: Polish
1. 既存の lint エラーがあれば修正
2. CLAUDE.md 更新（必要に応じて）
3. PR レビュー & マージ

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pylint が既存コードで大量エラー | Medium | disable 設定で段階的に有効化 |
| キャッシュ不整合 | Low | pyproject.toml ハッシュでキー管理 |
| CI 時間超過 (5分) | Low | 並列ジョブで高速化済み |

---

## Next Steps

```
/speckit.tasks
```
