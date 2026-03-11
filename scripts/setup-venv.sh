#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${1:-.venv}"

echo "Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install "PyYAML>=6.0" "tenacity>=8.0" "requests>=2.28"
echo "✅ venv created at $VENV_DIR"
