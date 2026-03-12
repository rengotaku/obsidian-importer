#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${BASE_DIR}/.venv/bin/python"
TEST_DATA_DIR="${BASE_DIR}/data/test"
FIXTURE_ZIP="${BASE_DIR}/tests/fixtures/claude_test.zip"
GOLDEN_DIR="${BASE_DIR}/tests/fixtures/golden"

echo "Preparing test data..."
"${BASE_DIR}/scripts/makefile/prepare-test-dirs.sh" "$TEST_DATA_DIR" "$FIXTURE_ZIP"

echo "Running full pipeline..."
cd "$BASE_DIR" && KEDRO_ENV=test "$PYTHON" -m kedro run --env=test

echo "Copying output to golden directory..."
rm -rf "$GOLDEN_DIR"
mkdir -p "$GOLDEN_DIR"
cp "$TEST_DATA_DIR/07_model_output/organized/"*.md "$GOLDEN_DIR/"
echo "Golden files updated: $(ls -1 "$GOLDEN_DIR/"*.md | wc -l) files"

echo "Cleaning up..."
rm -rf "$TEST_DATA_DIR"
echo "Golden files updated in tests/fixtures/golden/"
echo "Remember to commit the updated golden files!"
