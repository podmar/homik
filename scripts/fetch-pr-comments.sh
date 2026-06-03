#!/bin/bash
# Fetches all review comments from the current branch's open PR and writes
# them to docs/pr-comments.md, ready for the /review-comments skill.
#
# Usage:    chmod +x scripts/fetch-pr-comments.sh && ./scripts/fetch-pr-comments.sh
# Shortcut: echo "alias fetch-pr-comments='./scripts/fetch-pr-comments.sh'" >> ~/.zshrc && source ~/.zshrc
#           then run: fetch-pr-comments
#
# Requires: gh CLI (brew install gh) authenticated with gh auth login

set -euo pipefail

OUTPUT="docs/pr-comments.md"
mkdir -p "$(dirname "$OUTPUT")"  # Ensure parent directory exists

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI not installed. Run: brew install gh"
  exit 1
fi

PR_NUMBER=$(gh pr view --json number --jq '.number' 2>/dev/null) || {
  echo "Error: no open PR found for current branch."
  exit 1
}

REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
echo "Fetching comments for PR #$PR_NUMBER in $REPO..."

{
  echo "# PR #$PR_NUMBER Review Comments"
  echo ""

  # Inline review comments (attached to specific lines)
  INLINE_COUNT=$(gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --jq 'length')
  if [ "$INLINE_COUNT" -gt 0 ]; then
    echo "## Inline Comments"
    echo ""
    gh api "repos/$REPO/pulls/$PR_NUMBER/comments" --jq '.[] | "### \(.user.login) — \(.path) line \(.line // .original_line)\n\n\(.body)\n\n---\n"'
  fi

  # General PR comments (top-level, not attached to a line)
  GENERAL_COUNT=$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" --jq 'length')
  if [ "$GENERAL_COUNT" -gt 0 ]; then
    echo "## General Comments"
    echo ""
    gh api "repos/$REPO/issues/$PR_NUMBER/comments" --jq '.[] | "### \(.user.login)\n\n\(.body)\n\n---\n"'
  fi

} > "$OUTPUT"

echo "Done — written to $OUTPUT ($((INLINE_COUNT + GENERAL_COUNT)) comments)"
