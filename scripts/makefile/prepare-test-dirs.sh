#!/usr/bin/env bash
# Usage: prepare-test-dirs.sh <data_dir> <fixture_zip>
set -euo pipefail

DATA_DIR="${1:?Usage: prepare-test-dirs.sh <data_dir> <fixture_zip>}"
FIXTURE_ZIP="${2:?Usage: prepare-test-dirs.sh <data_dir> <fixture_zip>}"

rm -rf "$DATA_DIR/01_raw" "$DATA_DIR/02_intermediate" "$DATA_DIR/03_primary" "$DATA_DIR/04_feature" "$DATA_DIR/05_model_input" "$DATA_DIR/07_model_output"
mkdir -p "$DATA_DIR/01_raw/claude"
mkdir -p "$DATA_DIR/02_intermediate/parsed"
mkdir -p "$DATA_DIR/03_primary/transformed_knowledge"
mkdir -p "$DATA_DIR/03_primary/transformed_metadata"
mkdir -p "$DATA_DIR/04_feature/notes"
mkdir -p "$DATA_DIR/04_feature/review"
mkdir -p "$DATA_DIR/05_model_input/classified"
mkdir -p "$DATA_DIR/05_model_input/topic_extracted"
mkdir -p "$DATA_DIR/05_model_input/normalized"
mkdir -p "$DATA_DIR/05_model_input/cleaned"
mkdir -p "$DATA_DIR/07_model_output/organized"
echo '{}' > "$DATA_DIR/03_primary/transformed_knowledge/.placeholder.json"
echo '{}' > "$DATA_DIR/05_model_input/classified/.placeholder.json"
cp "$FIXTURE_ZIP" "$DATA_DIR/01_raw/claude/"
