#!/bin/bash
# Reads docs/pr-description.md and opens a PR against main using the gh CLI.
#
# Usage:    chmod +x scripts/create-pr.sh && ./scripts/create-pr.sh
# Shortcut: echo "alias create-pr='./scripts/create-pr.sh'" >> ~/.zshrc && source ~/.zshrc
#           then run: create-pr

set -euo pipefail

DESC_FILE="docs/pr-description.md"

if [ ! -f "$DESC_FILE" ]; then
  echo "Error: $DESC_FILE not found. Run /pr-description first."
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not installed. Run: brew install gh"
  exit 1
fi

TITLE=$(head -1 "$DESC_FILE" | sed 's/^## //')
BODY=$(tail -n +2 "$DESC_FILE")

gh pr create --base main --title "$TITLE" --body "$BODY"
