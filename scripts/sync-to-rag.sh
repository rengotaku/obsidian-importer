#!/usr/bin/env bash
# RAG システム (knowledge-rag) へのデータ同期スクリプト
#
# 使用方法:
#   ./scripts/sync-to-rag.sh                          # デフォルト設定で同期
#   RAG_HOST=192.168.1.100 ./scripts/sync-to-rag.sh   # ホスト指定
#   DRY_RUN=1 ./scripts/sync-to-rag.sh                # ドライラン
#
# 環境変数:
#   RAG_HOST      - RAG マシンのホスト名/IP (デフォルト: rag-server)
#   RAG_USER      - SSH ユーザー (デフォルト: 現在のユーザー)
#   RAG_DATA_DIR  - RAG 側のデータディレクトリ (デフォルト: ~/knowledge-rag/data/source)
#   DRY_RUN       - 1 でドライラン (デフォルト: 0)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RAG_HOST="${RAG_HOST:-rag-server}"
RAG_USER="${RAG_USER:-$(whoami)}"
RAG_DATA_DIR="${RAG_DATA_DIR:-~/knowledge-rag/data/source}"
DRY_RUN="${DRY_RUN:-0}"

SOURCE_DIR="${PROJECT_DIR}/data/03_primary/transformed_knowledge/"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Source directory not found: $SOURCE_DIR" >&2
    exit 1
fi

FILE_COUNT=$(find "$SOURCE_DIR" -name '*.json' | wc -l)
echo "Syncing ${FILE_COUNT} files from transformed_knowledge/ to ${RAG_USER}@${RAG_HOST}:${RAG_DATA_DIR}"

RSYNC_OPTS=(
    -avz
    --include='*.json'
    --exclude='*'
    --progress
)

if [ "$DRY_RUN" = "1" ]; then
    RSYNC_OPTS+=(--dry-run)
    echo "(dry-run mode)"
fi

rsync "${RSYNC_OPTS[@]}" \
    "$SOURCE_DIR" \
    "${RAG_USER}@${RAG_HOST}:${RAG_DATA_DIR}/"

echo "Done."
