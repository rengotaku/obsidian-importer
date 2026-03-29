#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

REVIEW_DIR="${BASE_DIR}/data/04_feature/review"
NOTES_DIR="${BASE_DIR}/data/04_feature/notes"
KNOWLEDGE_DIR="${BASE_DIR}/data/03_primary/transformed_knowledge"
PROMPT_FILE="${BASE_DIR}/scripts/prompts/reprocess-review.txt"

# Check prerequisites
if ! command -v claude &>/dev/null; then
    echo "Error: 'claude' command not found. Install Claude Code first."
    exit 1
fi

if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found: ${PROMPT_FILE}"
    exit 1
fi

if [ ! -d "$REVIEW_DIR" ] || [ -z "$(ls -A "$REVIEW_DIR" 2>/dev/null)" ]; then
    echo "No review files found in ${REVIEW_DIR}"
    exit 0
fi

# Collect review files and estimate tokens
files=()
total_chars=0
for md in "$REVIEW_DIR"/*.md; do
    [ -f "$md" ] || continue
    files+=("$md")
    chars=$(wc -m < "$md")
    total_chars=$((total_chars + chars))
done

if [ ${#files[@]} -eq 0 ]; then
    echo "No review files found."
    exit 0
fi

estimated_tokens=$((total_chars / 4))

echo "=== Review files to reprocess with Claude Code ==="
echo ""
for md in "${files[@]}"; do
    basename "$md"
done
echo ""
echo "Files:            ${#files[@]}"
echo "Total characters: ${total_chars}"
echo "Estimated tokens: ~${estimated_tokens}"
echo ""
read -r -p "Proceed? (Y/n): " confirm
if [[ "$confirm" =~ ^[Nn] ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# Read prompt template
prompt_template=$(cat "$PROMPT_FILE")

succeeded=0
failed=0

for md in "${files[@]}"; do
    filename=$(basename "$md")
    echo "Processing: ${filename}"

    # Extract metadata from YAML frontmatter
    file_id=$(grep '^file_id:' "$md" | sed 's/^file_id: *//')
    created=$(grep '^created:' "$md" | sed 's/^created: *//')
    source_provider=$(grep '^source_provider:' "$md" | sed 's/^source_provider: *//')

    if [ -z "$file_id" ]; then
        echo "  WARN: file_id not found, skipping"
        failed=$((failed + 1))
        continue
    fi

    # Extract original content (after "## 元のコンテンツ" separator)
    original_content=$(sed -n '/^## 元のコンテンツ$/,$ { /^## 元のコンテンツ$/d; p; }' "$md")
    if [ -z "$original_content" ]; then
        echo "  WARN: Original content section not found, skipping"
        failed=$((failed + 1))
        continue
    fi

    # Call Claude Code CLI
    user_message=$(printf '%s\n\n---\n\n%s' "$prompt_template" "$original_content")
    response=$(echo "$user_message" | claude -p --output-format text 2>/dev/null) || {
        echo "  ERROR: Claude Code CLI failed"
        failed=$((failed + 1))
        continue
    }

    if [ -z "$response" ]; then
        echo "  ERROR: Empty response from Claude Code"
        failed=$((failed + 1))
        continue
    fi

    # Parse response: extract title, summary, tags, content
    # Title: first line starting with "# "
    title=$(echo "$response" | grep -m1 '^# ' | sed 's/^# //')
    if [ -z "$title" ]; then
        echo "  WARN: Could not parse title from response, skipping"
        failed=$((failed + 1))
        continue
    fi

    # Summary: text after "## 要約" until next "##"
    summary=$(echo "$response" | sed -n '/^## 要約$/,/^## / { /^## /d; p; }' | sed '/^$/d' | head -1)

    # Tags: text after "## タグ" until next "##"
    tags_line=$(echo "$response" | sed -n '/^## タグ$/,/^## / { /^## /d; p; }' | sed '/^$/d' | head -1)

    # Content: everything after "## 内容"
    content_body=$(echo "$response" | sed -n '/^## 内容$/,$ { /^## 内容$/d; p; }')

    if [ -z "$content_body" ]; then
        echo "  WARN: Could not parse content from response, skipping"
        failed=$((failed + 1))
        continue
    fi

    # Parse tags into YAML array format
    tags_yaml="tags: []"
    if [ -n "$tags_line" ]; then
        tags_yaml="tags:"
        IFS=',' read -ra tag_arr <<< "$tags_line"
        for tag in "${tag_arr[@]}"; do
            tag=$(echo "$tag" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [ -n "$tag" ]; then
                # Escape double quotes in tag
                tag_escaped=$(echo "$tag" | sed 's/\\/\\\\/g; s/"/\\"/g')
                tags_yaml="${tags_yaml}
  - \"${tag_escaped}\""
            fi
        done
    fi

    # Escape title and summary for YAML
    title_escaped=$(echo "$title" | sed 's/\\/\//g; s/"/\\"/g')
    summary_escaped=$(echo "$summary" | sed 's/\\/\\\\/g; s/"/\\"/g')

    # Build output markdown
    output_md="---
title: \"${title_escaped}\"
created: ${created}
${tags_yaml}
summary: \"${summary_escaped}\"
source_provider: ${source_provider}
file_id: ${file_id}
normalized: true
---

${content_body}"

    # Sanitize filename (remove special chars, limit length)
    safe_title=$(echo "$title" | sed 's/[\\/:*?"<>|]/-/g; s/  */ /g' | cut -c1-100)
    output_filename="${safe_title}.md"

    # Write to notes directory
    mkdir -p "$NOTES_DIR"
    echo "$output_md" > "${NOTES_DIR}/${output_filename}"

    # Delete corresponding intermediate JSON
    json_path="${KNOWLEDGE_DIR}/${file_id}.json"
    if [ -f "$json_path" ]; then
        rm -f "$json_path"
    fi

    # Delete review file
    rm -f "$md"
    echo "  OK: → notes/${output_filename}"
    succeeded=$((succeeded + 1))
done

echo ""
echo "=== Results ==="
echo "Succeeded: ${succeeded}"
echo "Failed:    ${failed}"

if [ "$succeeded" -gt 0 ]; then
    echo ""
    echo "Next steps:"
    echo "  1. Review output in data/04_feature/notes/"
    echo "  2. Run 'make run' to execute organize pipeline"
fi
