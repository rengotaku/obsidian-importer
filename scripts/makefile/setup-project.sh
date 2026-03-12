#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${1:-.venv}"

echo "Creating Kedro data directories..."
mkdir -p data/01_raw/claude data/01_raw/openai data/01_raw/github
mkdir -p data/02_intermediate/parsed
mkdir -p data/03_primary/transformed data/03_primary/transformed_knowledge
mkdir -p data/04_feature/notes data/04_feature/review
mkdir -p data/05_model_input/classified
mkdir -p data/07_model_output/organized
mkdir -p logs

echo "Setting up local config..."
mkdir -p conf/local
if [ ! -f conf/local/parameters_organize.yml ]; then
    cp conf/base/parameters_organize.local.yml.example conf/local/parameters_organize.yml
    echo "  Created conf/local/parameters_organize.yml"
    echo "  Edit vault_base_path in this file to match your environment"
else
    echo "  conf/local/parameters_organize.yml already exists"
fi

echo "Setup complete. venv: $VENV_DIR"
