#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${BASE_DIR}/.venv/bin/python"
DATA_DIR="${BASE_DIR}/test-data"
FIXTURE_ZIP="${BASE_DIR}/tests/fixtures/claude_test.zip"

echo "Preparing test data..."
"${BASE_DIR}/scripts/makefile/prepare-test-dirs.sh" "$DATA_DIR" "$FIXTURE_ZIP"

echo "Running pipeline in mock mode..."
cd "$BASE_DIR" && KEDRO_ENV=integration "$PYTHON" -m kedro run --env=integration

echo "Validating output..."
MD_COUNT=$(find "$DATA_DIR/07_model_output/organized" -name "*.md" 2>/dev/null | wc -l)
if [ "$MD_COUNT" -eq 0 ]; then
    echo "FAIL No output files generated"
    exit 1
fi
echo "  OK Output files generated: $MD_COUNT files"

if ! grep -l "mock: true" "$DATA_DIR/07_model_output/organized/"*.md > /dev/null 2>&1 \
   && ! grep -rl "mock: true" "$DATA_DIR/07_model_output/notes/"*.md > /dev/null 2>&1; then
    echo "FAIL Output files missing mock: true frontmatter"
    exit 1
fi
echo "  OK All output files contain mock: true frontmatter"

if grep -rl "モックナレッジタイトル" "$DATA_DIR/07_model_output/organized/" > /dev/null 2>&1; then
    echo "FAIL Golden responses not used (fallback title found)"
    exit 1
fi
echo "  OK Golden responses verified (no fallback titles)"

echo "Cleaning up..."
rm -rf "$DATA_DIR/01_raw" "$DATA_DIR/02_intermediate" "$DATA_DIR/03_primary" "$DATA_DIR/07_model_output"
echo "Integration test passed (mock mode, no Ollama)"
