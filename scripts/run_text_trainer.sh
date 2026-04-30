#!/bin/bash
set -e

echo "===== Dataset Whitelist E2E Test ====="
echo "Container started at: $(date -u)"
echo "Arguments received: $@"
echo ""

python3 /workspace/scripts/verify_datasets.py "$@"
