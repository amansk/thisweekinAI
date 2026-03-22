#!/bin/bash
# Weekly AI papers curation — runs via launchd or Cowork every Sunday
# Calls Claude Code to fetch, score, build, and push the weekly edition

set -e

REPO_DIR="/Users/ak/code/thisweekinAI"
LOG_DIR="$REPO_DIR/logs"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run-${TIMESTAMP}.log"

cd "$REPO_DIR"

echo "=== Weekly curation run: $TIMESTAMP ===" | tee "$LOG_FILE"

claude -p "Run /curate" \
  --allowedTools "Bash,Read,Write,Edit,WebFetch,Glob,Grep" 2>&1 | tee -a "$LOG_FILE"

echo "=== Run complete: $(date) ===" | tee -a "$LOG_FILE"
