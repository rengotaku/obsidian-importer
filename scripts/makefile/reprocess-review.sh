#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

REVIEW_DIR="${BASE_DIR}/data/04_feature/review"
KNOWLEDGE_DIR="${BASE_DIR}/data/03_primary/transformed_knowledge"

if [ ! -d "$REVIEW_DIR" ] || [ -z "$(ls -A "$REVIEW_DIR" 2>/dev/null)" ]; then
    echo "No review files found in ${REVIEW_DIR}"
    exit 0
fi

count=0
for md in "$REVIEW_DIR"/*.md; do
    [ -f "$md" ] || continue

    file_id=$(grep '^file_id:' "$md" | sed 's/^file_id: *//')
    if [ -z "$file_id" ]; then
        echo "WARN: file_id not found in $(basename "$md"), skipping"
        continue
    fi

    json_path="${KNOWLEDGE_DIR}/${file_id}.json"
    if [ -f "$json_path" ]; then
        rm -f "$json_path"
        echo "  Deleted: $(basename "$json_path")"
    fi

    rm -f "$md"
    echo "  Deleted: $(basename "$md")"
    count=$((count + 1))
done

echo ""
echo "Cleared ${count} review files and corresponding intermediate data."
echo "Run 'make run' to reprocess."
