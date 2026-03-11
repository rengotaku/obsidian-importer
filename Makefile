# Obsidian Knowledge Base - ETL Pipeline Makefile
# ═══════════════════════════════════════════════════════════
#
# ⚠️  新しいターゲットを追加したら必ず ##@ コメントを付けること！
#     例: my-target: deps ##@ ターゲットの説明
#     `make help-claude` で CLAUDE.md 用コマンド一覧が自動生成される。
#     ##@ がないターゲットは一覧に含まれない。
#

BASE_DIR := $(shell pwd)
VENV_DIR := $(BASE_DIR)/.venv
PYTHON := $(VENV_DIR)/bin/python

# Kedro logging configuration (enables [file_id] prefix in logs)
export KEDRO_LOGGING_CONFIG := $(BASE_DIR)/conf/base/logging.yml

.PHONY: help help-claude setup setup-dev test coverage check lint ruff pylint mypy format format-check clean
.PHONY: rag-index rag-search rag-ask rag-status
.PHONY: test-e2e test-e2e-update-golden test-e2e-golden test-clean test-integration test-fixtures test-golden-responses
.PHONY: run kedro-run kedro-viz vault-preview vault-copy _check-ollama

help: ##@ コマンド一覧を表示
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Obsidian ETL Pipeline"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*##@' $(MAKEFILE_LIST) \
		| sed 's/\(^[a-zA-Z0-9_-]*\):.*##@ \(.*\)/\1\t\2/' \
		| awk -F'\t' '{printf "  %-24s %s\n", $$1, $$2}'
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"

# CLAUDE.md 用コマンドリファレンス出力（##@ コメントから自動生成）
help-claude:
	@echo '```bash'
	@grep -E '^[a-zA-Z0-9_-]+:.*##@' $(MAKEFILE_LIST) | sed 's/\(^[a-zA-Z0-9_-]*\):.*##@ \(.*\)/\1\t\2/' | awk -F'\t' '{printf "make %-24s# %s\n", $$1, $$2}'
	@echo '```'

setup: $(VENV_DIR)/bin/activate ##@ Python venv作成 + 依存関係インストール
	@echo "Creating Kedro data directories..."
	@mkdir -p data/01_raw/claude data/01_raw/openai data/01_raw/github
	@mkdir -p data/02_intermediate/parsed
	@mkdir -p data/03_primary/transformed data/03_primary/transformed_knowledge
	@mkdir -p data/07_model_output/notes data/07_model_output/organized
	@mkdir -p logs
	@echo ""
	@echo "Setting up local config..."
	@if [ ! -f conf/local/parameters_organize.yml ]; then \
		cp conf/base/parameters_organize.local.yml.example conf/local/parameters_organize.yml; \
		echo "  ✅ Created conf/local/parameters_organize.yml"; \
		echo "  📝 Edit vault_base_path in this file to match your environment"; \
	else \
		echo "  ⏭️  conf/local/parameters_organize.yml already exists"; \
	fi
	@echo ""
	@echo "✅ Setup complete. venv: $(VENV_DIR)"

$(VENV_DIR)/bin/activate:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Setting up Python virtual environment"
	@echo "═══════════════════════════════════════════════════════════"
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install "PyYAML>=6.0" "tenacity>=8.0" "requests>=2.28"
	@echo ""
	@echo "✅ venv created at $(VENV_DIR)"
	@echo "   To activate manually: source $(VENV_DIR)/bin/activate"

setup-dev: setup ##@ 開発用依存関係インストール
	@echo "Installing dev dependencies..."
	$(VENV_DIR)/bin/pip install -e ".[dev]"
	@echo "✅ Dev dependencies installed"

run: kedro-run ##@ パイプライン実行 [PIPELINE=import_claude|import_openai|import_github] [LIMIT=N]

kedro-run:
	@cd $(BASE_DIR) && $(PYTHON) -m kedro run \
		$(if $(PIPELINE),--pipeline $(PIPELINE),) \
		$(if $(GITHUB_URL),--params github_url=$(GITHUB_URL),) \
		$(if $(LIMIT),--params import.limit=$(LIMIT),) \
		$(if $(PARAMS),--params $(PARAMS),) \
		$(if $(FROM_NODES),--from-nodes $(FROM_NODES),) \
		$(if $(TO_NODES),--to-nodes $(TO_NODES),)

kedro-viz: ##@ DAG 可視化
	@cd $(BASE_DIR) && $(PYTHON) -m kedro viz

# テストフィクスチャZIP生成（JSONからZIPを組み立て）
CLAUDE_TEST_JSON := tests/fixtures/claude_test_conversations.json
CLAUDE_TEST_ZIP := tests/fixtures/claude_test.zip

test-fixtures: $(CLAUDE_TEST_ZIP)

$(CLAUDE_TEST_ZIP): $(CLAUDE_TEST_JSON)
	@echo "Building test fixture ZIP..."
	@cd tests/fixtures && $(PYTHON) -c "import zipfile, pathlib; z=zipfile.ZipFile('claude_test.zip','w',zipfile.ZIP_DEFLATED); z.write('claude_test_conversations.json','conversations.json'); z.close()"
	@echo "  OK $(CLAUDE_TEST_ZIP)"

# ───────────────────────────────────────────────────────────
# Helper: テストデータディレクトリ作成（内部用）
# Usage: $(call prepare-test-dirs,<data_dir>)
# ───────────────────────────────────────────────────────────
define prepare-test-dirs
	@rm -rf $(1)/01_raw $(1)/02_intermediate $(1)/03_primary $(1)/07_model_output
	@mkdir -p $(1)/01_raw/claude
	@mkdir -p $(1)/02_intermediate/parsed
	@mkdir -p $(1)/03_primary/transformed_knowledge
	@mkdir -p $(1)/03_primary/transformed_metadata
	@mkdir -p $(1)/07_model_output/classified
	@mkdir -p $(1)/07_model_output/topic_extracted
	@mkdir -p $(1)/07_model_output/normalized
	@mkdir -p $(1)/07_model_output/cleaned
	@mkdir -p $(1)/07_model_output/notes
	@mkdir -p $(1)/07_model_output/organized
	@mkdir -p $(1)/07_model_output/review
	@echo '{}' > $(1)/03_primary/transformed_knowledge/.placeholder.json
	@echo '{}' > $(1)/07_model_output/classified/.placeholder.json
	@cp tests/fixtures/claude_test.zip $(1)/01_raw/claude/
endef

_check-ollama:
	@curl -sf http://localhost:11434/api/tags > /dev/null || (echo "❌ Ollama is not running. Start it first."; exit 1)
	@echo "  ✅ Ollama is running"

# Kedro E2Eテスト（テスト用フィクスチャで LLM 処理まで実行）
# 前提: Ollama が起動していること
TEST_DATA_DIR := data/test
test-e2e: test-fixtures test-clean _check-ollama ##@ E2E テスト（ゴールデンファイル比較、要 Ollama）
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Kedro E2E Test (golden file comparison)"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Preparing test data..."
	$(call prepare-test-dirs,$(TEST_DATA_DIR))
	@echo "  ✅ Test data ready"
	@echo ""
	@echo "Running full pipeline..."
	@cd $(BASE_DIR) && KEDRO_ENV=test $(PYTHON) -m kedro run --env=test
	@echo ""
	@echo "Comparing with golden files..."
	@test -d tests/fixtures/golden && test $$(ls -1 tests/fixtures/golden/*.md 2>/dev/null | wc -l) -gt 0 \
		|| (echo "❌ Golden files not found. Run 'make test-e2e-update-golden' first."; rm -rf $(TEST_DATA_DIR); exit 1)
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m tests.e2e.golden_comparator \
		--actual $(TEST_DATA_DIR)/07_model_output/organized \
		--golden tests/fixtures/golden \
		--threshold 0.8
	@echo ""
	@echo "Cleaning up..."
	@rm -rf $(TEST_DATA_DIR)
	@echo ""
	@echo "  ✅ E2E test complete (golden file comparison passed)"

# ゴールデンファイル生成・更新
test-e2e-update-golden: test-fixtures _check-ollama
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Update Golden Files (E2E test reference)"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Preparing test data..."
	$(call prepare-test-dirs,$(TEST_DATA_DIR))
	@echo "  ✅ Test data ready"
	@echo ""
	@echo "Running full pipeline (including Organize)..."
	@cd $(BASE_DIR) && KEDRO_ENV=test $(PYTHON) -m kedro run --env=test
	@echo ""
	@echo "Copying output to golden directory..."
	@rm -rf tests/fixtures/golden
	@mkdir -p tests/fixtures/golden
	@cp $(TEST_DATA_DIR)/07_model_output/organized/*.md tests/fixtures/golden/
	@echo "  ✅ Golden files updated: $$(ls -1 tests/fixtures/golden/*.md | wc -l) files"
	@echo ""
	@echo "Cleaning up..."
	@rm -rf $(TEST_DATA_DIR)
	@echo ""
	@echo "  ✅ Golden files updated in tests/fixtures/golden/"
	@echo "  Remember to commit the updated golden files!"

test-e2e-golden: ##@ ゴールデンファイル品質テスト
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Golden File Quality Tests"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest tests.test_e2e_golden -v
	@echo ""
	@echo "✅ Golden file tests passed"

test-golden-responses: _check-ollama ##@ ゴールデンレスポンス再生成（要 Ollama）[MODEL=gemma3:12b]
	@echo "Generating golden responses..."
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) scripts/generate_golden_responses.py \
		$(if $(MODEL),--model $(MODEL),)
	@echo ""
	@echo "  ✅ Golden responses generated in tests/fixtures/golden_responses/"
	@echo "  Remember to commit the generated files!"

INTEGRATION_DATA_DIR := test-data

test-integration: test-fixtures ##@ 統合テスト（モックモード、Ollama 不要）
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Integration Test (Mock Mode - No Ollama Required)"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Preparing test data..."
	$(call prepare-test-dirs,$(INTEGRATION_DATA_DIR))
	@echo "  OK Test data ready"
	@echo ""
	@echo "Running pipeline in mock mode..."
	@cd $(BASE_DIR) && KEDRO_ENV=integration $(PYTHON) -m kedro run --env=integration
	@echo ""
	@echo "Validating output..."
	@test $$(find $(INTEGRATION_DATA_DIR)/07_model_output/organized -name "*.md" 2>/dev/null | wc -l) -gt 0 \
		|| (echo "FAIL No output files generated"; exit 1)
	@echo "  OK Output files generated: $$(find $(INTEGRATION_DATA_DIR)/07_model_output/organized -name "*.md" | wc -l) files"
	@grep -l "mock: true" $(INTEGRATION_DATA_DIR)/07_model_output/organized/*.md > /dev/null 2>&1 \
		|| grep -rl "mock: true" $(INTEGRATION_DATA_DIR)/07_model_output/notes/*.md > /dev/null 2>&1 \
		|| (echo "FAIL Output files missing mock: true frontmatter"; exit 1)
	@echo "  OK All output files contain mock: true frontmatter"
	@if grep -rl "モックナレッジタイトル" $(INTEGRATION_DATA_DIR)/07_model_output/organized/ > /dev/null 2>&1; then \
		echo "FAIL Golden responses not used (fallback title found)"; exit 1; \
	fi
	@echo "  OK Golden responses verified (no fallback titles)"
	@echo ""
	@echo "Cleaning up..."
	@rm -rf $(INTEGRATION_DATA_DIR)/01_raw $(INTEGRATION_DATA_DIR)/02_intermediate \
		$(INTEGRATION_DATA_DIR)/03_primary $(INTEGRATION_DATA_DIR)/07_model_output
	@echo ""
	@echo "  ✅ Integration test passed (mock mode, no Ollama)"

test: ##@ 全テスト実行（unit test）
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Kedro Pipeline Tests"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest discover -s tests -t . -v 2>&1
	@echo ""
	@echo "✅ All tests passed"

coverage: ##@ カバレッジ計測（≥80%）
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Test Coverage (Target: ≥80%)"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m coverage run --source=src/obsidian_etl -m unittest discover -s tests -t . 2>&1
	@cd $(BASE_DIR) && $(PYTHON) -m coverage report --fail-under=80
	@echo ""
	@echo "✅ Coverage ≥80% achieved"

check: ##@ Python 構文チェック
	@echo "Python構文チェック..."
	@find $(BASE_DIR)/src/obsidian_etl -name "*.py" -exec $(PYTHON) -m py_compile {} \;
	@echo "✅ 構文エラーなし"

ruff: ##@ ruff リンター実行
	@echo "Running ruff..."
	@$(VENV_DIR)/bin/ruff check src/obsidian_etl/
	@echo "✅ ruff passed"

pylint: ##@ pylint リンター実行
	@echo "Running pylint..."
	@$(VENV_DIR)/bin/pylint src/obsidian_etl/
	@echo "✅ pylint passed"

mypy: ##@ mypy 型チェック実行
	@echo "Running mypy..."
	@cd $(BASE_DIR)/src && $(VENV_DIR)/bin/mypy obsidian_etl/ rag/
	@echo "✅ mypy passed"

format-check: ##@ ruff フォーマットチェック
	@echo "Running ruff format check..."
	@$(VENV_DIR)/bin/ruff format --check src/ tests/
	@echo "✅ ruff format check passed"

format: ##@ ruff フォーマット適用
	@echo "Running ruff format..."
	@$(VENV_DIR)/bin/ruff format src/ tests/
	@echo "✅ ruff format applied"

lint: ruff pylint mypy format-check ##@ コード品質チェック (ruff + pylint + mypy + format-check)
	@echo "✅ All linters passed"

# E2Eテスト用データディレクトリ削除
test-clean:
	@echo "Cleaning test data directory..."
	@rm -rf $(TEST_DATA_DIR)
	@echo "✅ $(TEST_DATA_DIR) cleaned"

# 一時ファイル削除
clean:
	@echo "一時ファイル削除..."
	@find $(BASE_DIR)/src -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BASE_DIR)/.staging/@test
	@echo "✅ 完了"

rag-index: ##@ RAG インデックス作成 [VAULT=xxx]
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli index \
		$(if $(ACTION),--dry-run,) \
		$(if $(VAULT),--vault $(VAULT),)

rag-search: ##@ セマンティック検索 QUERY="..." [VAULT=xxx]
ifndef QUERY
	@echo "Error: QUERY is required"
	@echo "  Example: make rag-search QUERY=\"Kubernetes\""
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli search "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT),) \
		$(if $(TAG),--tag $(TAG),) \
		$(if $(TOP_K),--top-k $(TOP_K),)

rag-ask: ##@ Q&A QUERY="..." [VAULT=xxx]
ifndef QUERY
	@echo "Error: QUERY is required"
	@echo "  Example: make rag-ask QUERY=\"Kubernetes Pod とは？\""
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli ask "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT),) \
		$(if $(TAG),--tag $(TAG),)

rag-status: ##@ RAG インデックス状態表示
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli status \
		$(if $(FORMAT),--format $(FORMAT),)

vault-preview: ##@ Vault 出力先プレビュー（dry-run）
	@cd $(BASE_DIR) && kedro run --pipeline=organize_preview

vault-copy: ##@ Vault へファイルコピー [MODE=skip|overwrite|increment]
	@cd $(BASE_DIR) && kedro run --pipeline=organize_to_vault \
		$(if $(MODE),--params='{"organize.conflict_handling": "$(MODE)"}',)
