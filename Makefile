# Obsidian Knowledge Base - ETL Pipeline Makefile
# ═══════════════════════════════════════════════════════════

BASE_DIR := $(shell pwd)
VENV_DIR := $(BASE_DIR)/.venv
PYTHON := $(VENV_DIR)/bin/python
SESSION_DIR := $(BASE_DIR)/.staging/@session
LLM_EXPORTS_DIR := $(BASE_DIR)/.staging/@llm_exports
COMMA := ,

.PHONY: help setup setup-dev test test-fixtures coverage check lint clean
.PHONY: import organize status retry session-clean item-trace session-trace export-errors
.PHONY: rag-index rag-search rag-ask rag-status

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
	@echo "ETL Commands:"
	@echo "  import         Claude/ChatGPT会話インポート"
	@echo "                 INPUT=path [INPUT_TYPE=path|url] [PROVIDER=claude|openai|github] [DEBUG=1] [LIMIT=N] [DRY_RUN=1] [CHUNK=1]"
	@echo "  organize       ファイル整理・正規化"
	@echo "                 INPUT=path [DEBUG=1] [LIMIT=N] [DRY_RUN=1]"
	@echo "  status         セッション状態確認"
	@echo "                 [SESSION=xxx] [ALL=1] [JSON=1]"
	@echo "  retry          失敗アイテムのリトライ"
	@echo "                 SESSION=xxx [PHASE=import|organize] [DEBUG=1]"
	@echo "  session-clean  古いセッション削除"
	@echo "                 [DAYS=N] [DRY_RUN=1] [FORCE=1]"
	@echo "  item-trace     アイテム処理の詳細トレース"
	@echo "                 SESSION=xxx [TARGET=ALL|ERROR] [ITEM=xxx] [SHOW_CONTENT=1]"
	@echo "  session-trace  セッション詳細トレース（リアルタイム統計）"
	@echo "                 SESSION=xxx [JSON=1]"
	@echo "  export-errors  エラーアイテムをファイルに出力"
	@echo "                 SESSION=xxx → /tmp/{SESSION}/{skipped,failed}/"
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
	@echo "  make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude"
	@echo "  make import INPUT=chatgpt_export.zip PROVIDER=openai"
	@echo "  make import INPUT=file1.zip,file2.zip PROVIDER=openai  # Multiple files"
	@echo "  make import INPUT=https://github.com/user/repo/tree/master/_posts INPUT_TYPE=url PROVIDER=github"
	@echo "  make import SESSION=20260119_143052  # Resume existing session"
	@echo "  make organize INPUT=~/.staging/@index/"
	@echo "  make status ALL=1"
	@echo "  make retry SESSION=20260119_143052"
	@echo "  make item-trace SESSION=20260119_143052 ITEM=conversation_uuid"
	@echo "  make item-trace SESSION=20260119_143052 TARGET=ERROR"
	@echo "  make session-trace SESSION=20260119_143052"
	@echo "  make export-errors SESSION=20260119_143052"
	@echo "═══════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════
# Setup
# ═══════════════════════════════════════════════════════════

# Python venv作成 + 依存関係インストール
setup: $(VENV_DIR)/bin/activate
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
# ETL Pipeline Commands
# ═══════════════════════════════════════════════════════════

# Claude会話インポート
import:
ifndef SESSION
ifndef INPUT
	@echo "Error: INPUT is required for new sessions"
	@echo "  Example: make import INPUT=~/.staging/@llm_exports/claude/ PROVIDER=claude"
	@echo "  Example: make import INPUT=file1.zip,file2.zip PROVIDER=openai"
	@echo "  Example: make import INPUT=https://github.com/user/repo/tree/master/_posts INPUT_TYPE=url PROVIDER=github"
	@echo "  For Resume mode: make import SESSION=20260119_143052"
	@exit 1
endif
ifndef PROVIDER
	@echo "Error: PROVIDER is required for new sessions"
	@echo "  Example: make import INPUT=... PROVIDER=claude|openai|github"
	@echo "  For Resume mode: make import SESSION=20260119_143052"
	@exit 1
endif
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl import \
		$(foreach inp,$(subst $(COMMA), ,$(INPUT)),--input "$(inp)") \
		$(if $(INPUT_TYPE),--input-type $(INPUT_TYPE),) \
		$(if $(PROVIDER),--provider $(PROVIDER),) \
		$(if $(SESSION),--session $(SESSION),) \
		$(if $(DEBUG),--debug,) \
		$(if $(DRY_RUN),--dry-run,) \
		$(if $(LIMIT),--limit $(LIMIT),) \
		$(if $(CHUNK),--chunk,)

# ファイル整理・正規化
organize:
ifndef SESSION
ifndef INPUT
	@echo "Error: INPUT is required for new sessions"
	@echo "  Example: make organize INPUT=~/.staging/@index/"
	@echo "  For Resume mode: make organize SESSION=20260119_143052"
	@exit 1
endif
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl organize \
		$(if $(INPUT),--input "$(INPUT)",) \
		$(if $(SESSION),--session $(SESSION),) \
		$(if $(DEBUG),--debug,) \
		$(if $(DRY_RUN),--dry-run,) \
		$(if $(LIMIT),--limit $(LIMIT),)

# セッション状態確認
status:
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl status \
		$(if $(SESSION),--session $(SESSION),) \
		$(if $(ALL),--all,) \
		$(if $(JSON),--json,)

# 失敗アイテムのリトライ
retry:
ifndef SESSION
	@echo "Error: SESSION is required"
	@echo "  Example: make retry SESSION=20260119_143052"
	@echo ""
	@echo "Available sessions:"
	@ls -1 $(SESSION_DIR) 2>/dev/null | head -10 || echo "  (no sessions)"
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl retry --session "$(SESSION)" \
		$(if $(PHASE),--phase $(PHASE),) \
		$(if $(DEBUG),--debug,)

# 古いセッション削除
session-clean:
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl clean \
		$(if $(DAYS),--days $(DAYS),) \
		$(if $(DRY_RUN),--dry-run,) \
		$(if $(FORCE),--force,)

# アイテム処理の詳細トレース
item-trace:
ifndef SESSION
	@echo "Error: SESSION is required"
	@echo "  Example: make item-trace SESSION=20260119_143052 ITEM=conversation_uuid"
	@echo "  Example: make item-trace SESSION=20260119_143052 TARGET=ERROR"
	@echo "  Example: make item-trace SESSION=20260119_143052 TARGET=ERROR SHOW_ERROR_DETAILS=1"
	@echo ""
	@echo "Available sessions:"
	@ls -1 $(SESSION_DIR) 2>/dev/null | head -10 || echo "  (no sessions)"
	@exit 1
endif
	@TARGET_VALUE=$(if $(TARGET),$(TARGET),ALL); \
	if [ "$$TARGET_VALUE" = "ALL" ] && [ -z "$(ITEM)" ]; then \
		echo "Error: ITEM is required when TARGET=ALL"; \
		echo "  Example: make item-trace SESSION=20260119_143052 ITEM=conversation_uuid"; \
		echo "  Or use: make item-trace SESSION=20260119_143052 TARGET=ERROR"; \
		exit 1; \
	fi; \
	cd $(BASE_DIR) && $(PYTHON) -m src.etl trace --session "$(SESSION)" --target "$$TARGET_VALUE" \
		$(if $(ITEM),--item "$(ITEM)",) \
		$(if $(SHOW_CONTENT),--show-content,) \
		$(if $(SHOW_ERROR_DETAILS),--show-error-details,)

# セッション詳細トレース（リアルタイム統計）
session-trace:
ifndef SESSION
	@echo "Error: SESSION is required"
	@echo "  Example: make session-trace SESSION=20260119_143052"
	@echo "  Example: make session-trace SESSION=20260119_143052 JSON=1"
	@echo ""
	@echo "Available sessions:"
	@ls -1 $(SESSION_DIR) 2>/dev/null | head -10 || echo "  (no sessions)"
	@exit 1
endif
	@cd $(BASE_DIR) && $(PYTHON) -m src.etl session-trace --session "$(SESSION)" \
		$(if $(JSON),--json,)

# エラーアイテムをファイルに出力
export-errors:
ifndef SESSION
	@echo "Error: SESSION is required"
	@echo "  Example: make export-errors SESSION=20260119_143052"
	@echo ""
	@echo "Available sessions:"
	@ls -1 $(SESSION_DIR) 2>/dev/null | head -10 || echo "  (no sessions)"
	@exit 1
endif
	@echo "Exporting skipped and failed items from session $(SESSION)..."
	@OUTPUT_DIR="/tmp/$(SESSION)"; \
	SKIPPED_DIR="$$OUTPUT_DIR/skipped"; \
	FAILED_DIR="$$OUTPUT_DIR/failed"; \
	mkdir -p "$$SKIPPED_DIR" "$$FAILED_DIR"; \
	EXTRACT_OUTPUT="$(SESSION_DIR)/$(SESSION)/import/extract/output"; \
	TRANSFORM_STEPS="$(SESSION_DIR)/$(SESSION)/import/transform/steps.jsonl"; \
	if [ ! -f "$$TRANSFORM_STEPS" ]; then \
		echo "Error: $$TRANSFORM_STEPS not found"; \
		exit 1; \
	fi; \
	EXTRACT_JSONL=$$(find "$$EXTRACT_OUTPUT" -name "*.jsonl" | head -1); \
	if [ -z "$$EXTRACT_JSONL" ]; then \
		echo "Error: No JSONL file found in $$EXTRACT_OUTPUT"; \
		exit 1; \
	fi; \
	echo "Source: $$EXTRACT_JSONL"; \
	echo ""; \
	echo "Exporting skipped items..."; \
	cat "$$TRANSFORM_STEPS" | jq -r 'select(.status == "filtered") | .item_id' | sort -u | while read item_id; do \
		cat "$$EXTRACT_JSONL" | jq -s "map(select(.item_id == \"$$item_id\")) | last" > "$$SKIPPED_DIR/$$item_id.json"; \
		if [ -s "$$SKIPPED_DIR/$$item_id.json" ] && [ "$$(cat "$$SKIPPED_DIR/$$item_id.json")" != "null" ]; then \
			cat "$$SKIPPED_DIR/$$item_id.json" | $(PYTHON) src/etl/cli/utils/format_conversation.py > "$$SKIPPED_DIR/$$item_id.txt" 2>&1 || \
			echo "Error: Failed to format conversation" > "$$SKIPPED_DIR/$$item_id.txt"; \
			echo "  $$SKIPPED_DIR/$$item_id.txt"; \
		fi; \
	done; \
	SKIPPED_COUNT=$$(ls "$$SKIPPED_DIR"/*.txt 2>/dev/null | wc -l); \
	echo ""; \
	echo "Exporting failed items..."; \
	cat "$$TRANSFORM_STEPS" | jq -r 'select(.status == "failed") | .item_id' | sort -u | while read item_id; do \
		cat "$$EXTRACT_JSONL" | jq -s "map(select(.item_id == \"$$item_id\")) | last" > "$$FAILED_DIR/$$item_id.json"; \
		if [ -s "$$FAILED_DIR/$$item_id.json" ] && [ "$$(cat "$$FAILED_DIR/$$item_id.json")" != "null" ]; then \
			cat "$$FAILED_DIR/$$item_id.json" | $(PYTHON) src/etl/cli/utils/format_conversation.py > "$$FAILED_DIR/$$item_id.txt" 2>&1 || \
			echo "Error: Failed to format conversation" > "$$FAILED_DIR/$$item_id.txt"; \
			echo "  $$FAILED_DIR/$$item_id.txt"; \
		fi; \
	done; \
	FAILED_COUNT=$$(ls "$$FAILED_DIR"/*.txt 2>/dev/null | wc -l); \
	echo ""; \
	echo "═══════════════════════════════════════════════════════════"; \
	echo "Export completed!"; \
	echo "  Output: $$OUTPUT_DIR"; \
	echo "  Skipped: $$SKIPPED_COUNT items (.txt + .json)"; \
	echo "  Failed: $$FAILED_COUNT items (.txt + .json)"; \
	echo "═══════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════════════

# 全テスト実行（統合テストはスキップ）
test:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  ETL Pipeline Tests (Unit + Mocked)"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && $(PYTHON) -m unittest discover -s src/etl/tests -t . -v 2>&1
	@echo ""
	@echo "✅ All tests passed"

# 統合テスト実行（実際のLLMを使用）
test-fixtures:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Integration Tests (Real LLM)"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && RUN_INTEGRATION_TESTS=1 $(PYTHON) -m unittest discover -s src/etl/tests -t . -v 2>&1
	@echo ""
	@echo "✅ Integration tests passed"

# テストカバレッジ計測
coverage:
	@echo "═══════════════════════════════════════════════════════════"
	@echo "  Test Coverage (Target: ≥80%)"
	@echo "═══════════════════════════════════════════════════════════"
	@cd $(BASE_DIR) && $(PYTHON) -m coverage run --source=src/etl -m unittest discover -s src/etl/tests -t . 2>&1
	@cd $(BASE_DIR) && $(PYTHON) -m coverage report --fail-under=80
	@echo ""
	@echo "✅ Coverage ≥80% achieved"

# Python構文チェック
check:
	@echo "Python構文チェック..."
	@find $(BASE_DIR)/src/etl -name "*.py" -exec $(PYTHON) -m py_compile {} \;
	@echo "✅ 構文エラーなし"

# コード品質チェック (ruff)
lint:
	@echo "Running ruff lint..."
	@timeout 10 $(VENV_DIR)/bin/ruff check src/etl/ || { \
		echo "❌ Lint failed or timed out"; \
		exit 1; \
	}
	@echo "✅ Lint passed"

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
