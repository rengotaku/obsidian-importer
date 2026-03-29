# Obsidian Knowledge Base - ETL Pipeline Makefile
#
# 新しいターゲットを追加したら必ず ##@ コメントを付けること！
# 例: my-target: deps ##@ ターゲットの説明
# `make help-claude` で CLAUDE.md 用コマンド一覧が自動生成される。

BASE_DIR := $(shell pwd)
VENV_DIR := $(BASE_DIR)/.venv
PYTHON := $(VENV_DIR)/bin/python

export KEDRO_LOGGING_CONFIG := $(BASE_DIR)/conf/base/logging.yml

.PHONY: all help help-claude setup setup-dev run kedro-run kedro-viz
.PHONY: test test-fixtures test-e2e test-e2e-update-golden test-e2e-golden
.PHONY: test-golden-responses test-integration test-clean
.PHONY: coverage check lint ruff pylint mypy format format-check clean
.PHONY: rag-index rag-search rag-ask rag-status vault-preview vault-copy
.PHONY: reprocess-review
.PHONY: _check-ollama

all: help

help: ##@ コマンド一覧を表示
	@echo "Obsidian ETL Pipeline"
	@grep -E '^[a-zA-Z0-9_-]+:.*##@' $(MAKEFILE_LIST) | sed 's/\(^[a-zA-Z0-9_-]*\):.*##@ \(.*\)/\1\t\2/' | awk -F'\t' '{printf "  %-24s %s\n", $$1, $$2}'

help-claude: ##@ CLAUDE.md 用コマンドリファレンス出力
	@echo '```bash'
	@grep -E '^[a-zA-Z0-9_-]+:.*##@' $(MAKEFILE_LIST) | sed 's/\(^[a-zA-Z0-9_-]*\):.*##@ \(.*\)/\1\t\2/' | awk -F'\t' '{printf "make %-24s# %s\n", $$1, $$2}'
	@echo '```'

# ── Setup ──────────────────────────────────────────────────

setup: $(VENV_DIR)/bin/activate ##@ Python venv作成 + 依存関係インストール
	@bash scripts/makefile/setup-project.sh $(VENV_DIR)

$(VENV_DIR)/bin/activate:
	@bash scripts/makefile/setup-venv.sh $(VENV_DIR)

setup-dev: setup ##@ 開発用依存関係インストール
	$(VENV_DIR)/bin/pip install -e ".[dev]"

# ── Kedro Pipeline ────────────────────────────────────────

run: kedro-run ##@ パイプライン実行 [PIPELINE=import_claude|import_openai|import_github] [LIMIT=N]

kedro-run:
	@cd $(BASE_DIR) && $(PYTHON) -m kedro run $(if $(PIPELINE),--pipeline $(PIPELINE),) $(if $(GITHUB_URL),--params github_url=$(GITHUB_URL),) $(if $(LIMIT),--params import.limit=$(LIMIT),) $(if $(PARAMS),--params $(PARAMS),) $(if $(FROM_NODES),--from-nodes $(FROM_NODES),) $(if $(TO_NODES),--to-nodes $(TO_NODES),)

kedro-viz: ##@ DAG 可視化
	@cd $(BASE_DIR) && $(PYTHON) -m kedro viz

reprocess-review: ##@ review ファイルを削除して再処理対象に戻す
	@bash scripts/makefile/reprocess-review.sh

# ── Test Fixtures ─────────────────────────────────────────

CLAUDE_TEST_JSON := tests/fixtures/claude_test_conversations.json
CLAUDE_TEST_ZIP := tests/fixtures/claude_test.zip

test-fixtures: $(CLAUDE_TEST_ZIP)

$(CLAUDE_TEST_ZIP): $(CLAUDE_TEST_JSON)
	@echo "Building test fixture ZIP..."
	@cd tests/fixtures && $(PYTHON) -c "import zipfile; z=zipfile.ZipFile('claude_test.zip','w',zipfile.ZIP_DEFLATED); z.write('claude_test_conversations.json','conversations.json'); z.close()"

# ── E2E / Integration Tests ──────────────────────────────

_check-ollama:
	@curl -sf http://localhost:11434/api/tags > /dev/null || (echo "Ollama is not running. Start it first."; exit 1)

TEST_DATA_DIR := data/test

test-e2e: test-fixtures test-clean _check-ollama ##@ E2E テスト（ゴールデンファイル比較、要 Ollama）
	@bash scripts/makefile/test-e2e.sh

test-e2e-update-golden: test-fixtures _check-ollama ##@ ゴールデンファイル生成・更新（要 Ollama）
	@bash scripts/makefile/test-e2e-update-golden.sh

test-e2e-golden: ##@ ゴールデンファイル品質テスト
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest tests.test_e2e_golden -v

test-golden-responses: _check-ollama ##@ ゴールデンレスポンス再生成（要 Ollama）[MODEL=gemma3:12b]
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) scripts/generate_golden_responses.py $(if $(MODEL),--model $(MODEL),)

INTEGRATION_DATA_DIR := test-data

test-integration: test-fixtures ##@ 統合テスト（モックモード、Ollama 不要）
	@bash scripts/makefile/test-integration.sh

# ── Unit Test / Coverage ──────────────────────────────────

test: ##@ 全テスト実行（unit test）
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest discover -s tests -t . -v 2>&1

coverage: ##@ カバレッジ計測（≥80%）
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m coverage run --source=src/obsidian_etl -m unittest discover -s tests -t . 2>&1
	@cd $(BASE_DIR) && $(PYTHON) -m coverage report --fail-under=80

# ── Linting ───────────────────────────────────────────────

check: ##@ Python 構文チェック
	@find $(BASE_DIR)/src/obsidian_etl -name "*.py" -exec $(PYTHON) -m py_compile {} \;

ruff: ##@ ruff リンター実行
	@$(VENV_DIR)/bin/ruff check src/obsidian_etl/

pylint: ##@ pylint リンター実行
	@$(VENV_DIR)/bin/pylint src/obsidian_etl/

mypy: ##@ mypy 型チェック実行
	@cd $(BASE_DIR)/src && $(VENV_DIR)/bin/mypy obsidian_etl/ rag/

format-check: ##@ ruff フォーマットチェック
	@$(VENV_DIR)/bin/ruff format --check src/ tests/

format: ##@ ruff フォーマット適用
	@$(VENV_DIR)/bin/ruff format src/ tests/

lint: ruff pylint mypy format-check ##@ コード品質チェック (ruff + pylint + mypy + format-check)

# ── Cleanup ───────────────────────────────────────────────

test-clean:
	@rm -rf $(TEST_DATA_DIR)

clean: ##@ 一時ファイル削除
	@find $(BASE_DIR)/src -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BASE_DIR)/.staging/@test

# ── RAG ───────────────────────────────────────────────────

rag-index: ##@ RAG インデックス作成 [VAULT=xxx]
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli index $(if $(ACTION),--dry-run,) $(if $(VAULT),--vault $(VAULT),)

rag-search: ##@ セマンティック検索 QUERY="..." [VAULT=xxx]
	@test -n "$(QUERY)" || (echo "Error: QUERY is required. Example: make rag-search QUERY=\"Kubernetes\""; exit 1)
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli search "$(QUERY)" $(if $(VAULT),--vault $(VAULT),) $(if $(TAG),--tag $(TAG),) $(if $(TOP_K),--top-k $(TOP_K),)

rag-ask: ##@ Q&A QUERY="..." [VAULT=xxx]
	@test -n "$(QUERY)" || (echo "Error: QUERY is required. Example: make rag-ask QUERY=\"Kubernetes Pod とは？\""; exit 1)
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli ask "$(QUERY)" $(if $(VAULT),--vault $(VAULT),) $(if $(TAG),--tag $(TAG),)

rag-status: ##@ RAG インデックス状態表示
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli status $(if $(FORMAT),--format $(FORMAT),)

# ── Vault Output ──────────────────────────────────────────

vault-preview: ##@ Vault 出力先プレビュー（dry-run）
	@cd $(BASE_DIR) && kedro run --pipeline=organize_preview

vault-copy: ##@ Vault へファイルコピー [MODE=skip|overwrite|increment]
	@cd $(BASE_DIR) && kedro run --pipeline=organize_to_vault $(if $(MODE),--params='{"organize.conflict_handling": "$(MODE)"}',)
