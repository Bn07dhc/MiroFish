#!/bin/bash
# Ingest SimLab corpus into Qdrant
# Usage: ./ingest.sh [corpus_dir]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")/backend"

export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"

python3 -c "
import sys
sys.path.insert(0, '$BACKEND_DIR')
from app.services.simlab.ingest import ingest_corpus
stats = ingest_corpus('${1:-$SCRIPT_DIR}')
print()
print('=== Ingest Complete ===')
total = sum(stats.values())
print(f'Total: {total} chunks across {len(stats)} categories')
for cat, count in sorted(stats.items()):
    print(f'  {cat}: {count}')
"
