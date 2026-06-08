#!/bin/bash
# Runs Ruff and Pyright on the backend and writes results to docs/lint-report.md.
#
# Assumptions:
#   - Run from the project root (not from backend/)
#   - `uv` is installed and on PATH (https://docs.astral.sh/uv/)
#   - Python dependencies are already synced (run `uv sync` in backend/ if not)
#
# Usage:    chmod +x scripts/run-lint.sh && ./scripts/run-lint.sh
# Shortcut: add alias to ~/.zshrc — see output at end of script
#           alias run-lint='./scripts/run-lint.sh'
#
# Output:   docs/lint-report.md

set -uo pipefail  # No -e: lint failures are non-zero exits we want to capture

OUTPUT="docs/lint-report.md"
BACKEND_DIR="backend"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S %Z")

mkdir -p "$(dirname "$OUTPUT")"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv not found on PATH. Install from https://docs.astral.sh/uv/"
  exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "Error: $BACKEND_DIR/ not found. Run this script from the project root."
  exit 1
fi

echo "Running Ruff..."
RUFF_OUTPUT=$(cd "$BACKEND_DIR" && uv run ruff check . 2>&1) || true

echo "Running Pyright..."
PYRIGHT_OUTPUT=$(cd "$BACKEND_DIR" && uv run pyright 2>&1) || true

{
  echo "# Lint Report"
  echo ""
  echo "Generated: $TIMESTAMP"
  echo ""
  echo "---"
  echo ""
  echo "## Ruff"
  echo ""
  if [ -z "$RUFF_OUTPUT" ]; then
    echo "_No issues found._"
  else
    echo '```'
    echo "$RUFF_OUTPUT"
    echo '```'
  fi
  echo ""
  echo "---"
  echo ""
  echo "## Pyright"
  echo ""
  if [ -z "$PYRIGHT_OUTPUT" ]; then
    echo "_No issues found._"
  else
    echo '```'
    echo "$PYRIGHT_OUTPUT"
    echo '```'
  fi
} > "$OUTPUT"

RUFF_ISSUES=$(echo "$RUFF_OUTPUT" | grep -c '\.py' 2>/dev/null || echo 0)
PYRIGHT_ISSUES=$(echo "$PYRIGHT_OUTPUT" | grep -c 'error\|warning' 2>/dev/null || echo 0)

echo ""
echo "Done — written to $OUTPUT"
echo "  Ruff:    ~$RUFF_ISSUES file(s) with issues"
echo "  Pyright: ~$PYRIGHT_ISSUES diagnostic(s)"
echo ""
echo "Run /fix-lint in Claude Code to work through the issues."
