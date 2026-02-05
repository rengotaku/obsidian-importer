# Obsidian Knowledge Base - ETL Pipeline Makefile
# ═══════════════════════════════════════════════════════════

BASE_DIR := $(shell pwd)
VENV_DIR := $(BASE_DIR)/.venv
PYTHON := $(VENV_DIR)/bin/python
SESSION_DIR := $(BASE_DIR)/.staging/@session
LLM_EXPORTS_DIR := $(BASE_DIR)/.staging/@llm_exports
COMMA := ,

.PHONY: help setup setup-dev test coverage check lint clean
.PHONY: rag-index rag-search rag-ask rag-status
.PHONY: test-e2e test-e2e-update-golden test-clean
.PHONY: kedro-run kedro-test kedro-viz

# ═══════════════════════════════════════════════════════════
# Help
# ═══════════════════════════════════════════════════════════

help:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Obsidian ETL Pipeline"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "Setup:"
	@echo "  setup          Python venv作成 + 依存関係インストール"
	@echo "  setup-dev      開発用依存関係インストール (ruff, coverage)"
	@echo ""
	@echo "Kedro Pipeline:"
	@echo "  kedro-run      Kedro パイプライン実行"
	@echo "                 [PIPELINE=import_claude|import_openai|import_github]"
	@echo "                 [PARAMS='...'] [FROM_NODES=...] [TO_NODES=...]"
	@echo "  kedro-test     Kedro テスト実行"
	@echo "  kedro-viz      DAG 可視化"
	@echo "  test-e2e       E2Eテスト（ゴールデンファイル比較、閾値80%）"
	@echo "  test-e2e-update-golden"
	@echo "                 ゴールデンファイル生成・更新（LLMモデル/プロンプト変更時）"
	@echo "  test-clean     E2Eテスト用データ削除"
	@echo ""
	@echo "Testing:"
	@echo "  test           全テスト実行"
	@echo "  coverage       テストカバレッジ計測 (≥80%)"
	@echo "  check          Python構文チェック"
	@echo "  lint           コード品質チェック (ruff)"
	@echo ""
	@echo "RAG (Semantic Search):"
	@echo "  rag-index      インデックス作成 [VAULT=xxx]"
	@echo "  rag-search     セマンティック検索 QUERY=\"...\" [VAULT=xxx]"
	@echo "  rag-ask        Q&A QUERY=\"...\" [VAULT=xxx]"
	@echo "  rag-status     インデックス状態"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                                              # 初回セットアップ"
	@echo "  make kedro-run PIPELINE=import_claude                   # Claude インポート"
	@echo "  make kedro-run PIPELINE=import_openai                   # ChatGPT インポート"
	@echo "  make kedro-run PIPELINE=import_github                   # GitHub Jekyll インポート"
	@echo "  make kedro-test                                         # Kedro テスト実行"
	@echo "  make kedro-viz                                          # DAG 可視化"
	@echo "  make test                                               # 全テスト実行"
	@echo "═══════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════
# Setup
# ═══════════════════════════════════════════════════════════

# Python venv作成 + 依存関係インストール
setup: $(VENV_DIR)/bin/activate
	@echo "Creating Kedro data directories..."
	@mkdir -p data/01_raw/claude data/01_raw/openai data/01_raw/github
	@mkdir -p data/02_intermediate/parsed
	@mkdir -p data/03_primary/transformed data/03_primary/transformed_knowledge
	@mkdir -p data/07_model_output/notes data/07_model_output/organized
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

# 開発用依存関係インストール
setup-dev: setup
	@echo "Installing dev dependencies..."
	$(VENV_DIR)/bin/pip install "ruff>=0.1.0" "coverage>=7.0"
	@echo "✅ Dev dependencies installed"

# ═══════════════════════════════════════════════════════════
# Kedro Pipeline Commands
# ═══════════════════════════════════════════════════════════

# Kedro パイプライン実行
kedro-run:
	@cd $(BASE_DIR) && $(PYTHON) -m kedro run \
		$(if $(PIPELINE),--pipeline $(PIPELINE),) \
		$(if $(PARAMS),--params '$(PARAMS)',) \
		$(if $(FROM_NODES),--from-nodes $(FROM_NODES),) \
		$(if $(TO_NODES),--to-nodes $(TO_NODES),)

# Kedro テスト実行（新パッケージ）
kedro-test:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Kedro Pipeline Tests"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest discover -s tests -t . -v 2>&1
	@echo ""
	@echo "✅ Kedro tests passed"

# Kedro DAG 可視化
kedro-viz:
	@cd $(BASE_DIR) && $(PYTHON) -m kedro viz

# Kedro E2Eテスト（テスト用フィクスチャで LLM 処理まで実行）
# 前提: Ollama が起動していること
TEST_DATA_DIR := data/test
test-e2e: test-clean
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Kedro E2E Test (golden file comparison)"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "[1/5] Checking Ollama..."
	@curl -sf http://localhost:11434/api/tags > /dev/null || (echo "❌ Ollama is not running. Start it first."; exit 1)
	@echo "  ✅ Ollama is running"
	@echo ""
	@echo "[2/5] Preparing test data..."
	@rm -rf $(TEST_DATA_DIR)
	@mkdir -p $(TEST_DATA_DIR)/01_raw/claude
	@mkdir -p $(TEST_DATA_DIR)/02_intermediate/parsed
	@mkdir -p $(TEST_DATA_DIR)/03_primary/transformed_knowledge
	@mkdir -p $(TEST_DATA_DIR)/03_primary/transformed_metadata
	@mkdir -p $(TEST_DATA_DIR)/07_model_output/notes
	@mkdir -p $(TEST_DATA_DIR)/07_model_output/organized
	@echo '{}' > $(TEST_DATA_DIR)/03_primary/transformed_knowledge/.placeholder.json
	@cp tests/fixtures/claude_test.zip $(TEST_DATA_DIR)/01_raw/claude/
	@echo "  ✅ Test data ready"
	@echo ""
	@echo "[3/5] Running pipeline to format_markdown..."
	@cd $(BASE_DIR) && $(PYTHON) -m kedro run --env=test --to-nodes=format_markdown
	@echo ""
	@echo "[4/5] Comparing with golden files..."
	@test -d tests/fixtures/golden && test $$(ls -1 tests/fixtures/golden/*.md 2>/dev/null | wc -l) -gt 0 \
		|| (echo "❌ Golden files not found. Run 'make test-e2e-update-golden' first."; rm -rf $(TEST_DATA_DIR); exit 1)
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m tests.e2e.golden_comparator \
		--actual $(TEST_DATA_DIR)/07_model_output/notes \
		--golden tests/fixtures/golden \
		--threshold 0.8
	@echo ""
	@echo "[5/5] Cleaning up..."
	@rm -rf $(TEST_DATA_DIR)
	@echo "  ✅ Test data cleaned"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ✅ E2E test complete (golden file comparison passed)"
	@echo "═══════════════════════════════════════════════════════════"

# ゴールデンファイル生成・更新
test-e2e-update-golden:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Update Golden Files (E2E test reference)"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo "[1/5] Checking Ollama..."
	@curl -sf http://localhost:11434/api/tags > /dev/null || (echo "❌ Ollama is not running. Start it first."; exit 1)
	@echo "  ✅ Ollama is running"
	@echo ""
	@echo "[2/5] Preparing test data..."
	@rm -rf $(TEST_DATA_DIR)
	@mkdir -p $(TEST_DATA_DIR)/01_raw/claude
	@mkdir -p $(TEST_DATA_DIR)/02_intermediate/parsed
	@mkdir -p $(TEST_DATA_DIR)/03_primary/transformed_knowledge
	@mkdir -p $(TEST_DATA_DIR)/03_primary/transformed_metadata
	@mkdir -p $(TEST_DATA_DIR)/07_model_output/notes
	@mkdir -p $(TEST_DATA_DIR)/07_model_output/organized
	@echo '{}' > $(TEST_DATA_DIR)/03_primary/transformed_knowledge/.placeholder.json
	@cp tests/fixtures/claude_test.zip $(TEST_DATA_DIR)/01_raw/claude/
	@echo "  ✅ Test data ready"
	@echo ""
	@echo "[3/5] Running pipeline to format_markdown..."
	@cd $(BASE_DIR) && $(PYTHON) -m kedro run --env=test --to-nodes=format_markdown
	@echo ""
	@echo "[4/5] Copying output to golden directory..."
	@rm -rf tests/fixtures/golden
	@mkdir -p tests/fixtures/golden
	@cp $(TEST_DATA_DIR)/07_model_output/notes/*.md tests/fixtures/golden/
	@echo "  ✅ Golden files updated: $$(ls -1 tests/fixtures/golden/*.md | wc -l) files"
	@echo ""
	@echo "[5/5] Cleaning up..."
	@rm -rf $(TEST_DATA_DIR)
	@echo "  ✅ Test data cleaned"
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ✅ Golden files updated in tests/fixtures/golden/"
	@echo "  Remember to commit the updated golden files!"
	@echo "═══════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════════════

# 全テスト実行（Kedro パイプライン）
test:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Kedro Pipeline Tests"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m unittest discover -s tests -t . -v 2>&1
	@echo ""
	@echo "✅ All tests passed"

# テストカバレッジ計測
coverage:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Test Coverage (Target: ≥80%)"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && PYTHONPATH=$(BASE_DIR)/src $(PYTHON) -m coverage run --source=src/obsidian_etl -m unittest discover -s tests -t . 2>&1
	@cd $(BASE_DIR) && $(PYTHON) -m coverage report --fail-under=80
	@echo ""
	@echo "✅ Coverage ≥80% achieved"

# Python構文チェック
check:
	@echo "Python構文チェック..."
	@find $(BASE_DIR)/src/obsidian_etl -name "*.py" -exec $(PYTHON) -m py_compile {} \;
	@echo "✅ 構文エラーなし"

# コード品質チェック (ruff)
lint:
	@echo "Running ruff lint..."
	@timeout 10 $(VENV_DIR)/bin/ruff check src/obsidian_etl/ || { \
		echo "❌ Lint failed or timed out"; \
		exit 1; \
	}
	@echo "✅ Lint passed"

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

# ═══════════════════════════════════════════════════════════
# RAG (Semantic Search)
# ═══════════════════════════════════════════════════════════

rag-index:
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli index \
		$(if $(ACTION),--dry-run,) \
		$(if $(VAULT),--vault $(VAULT),)

rag-search:
ifndef QUERY
	@echo "Error: QUERY is required"
	@echo "  Example: make rag-search QUERY=\"Kubernetes\""
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli search "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT),) \
		$(if $(TAG),--tag $(TAG),) \
		$(if $(TOP_K),--top-k $(TOP_K),)

rag-ask:
ifndef QUERY
	@echo "Error: QUERY is required"
	@echo "  Example: make rag-ask QUERY=\"Kubernetes Pod とは？\""
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli ask "$(QUERY)" \
		$(if $(VAULT),--vault $(VAULT),) \
		$(if $(TAG),--tag $(TAG),)

rag-status:
	@cd $(BASE_DIR) && $(PYTHON) -m src.rag.cli status \
		$(if $(FORMAT),--format $(FORMAT),)
