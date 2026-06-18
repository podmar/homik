#!/bin/bash
# Runs the pytest suite against the backend and writes the full output to
# docs/test-report.txt. The file is plain text so Claude Code can read it
# directly with /fix-test.
#
# Assumptions:
#   - Run from the project root (not from backend/)
#   - `uv` is installed and on PATH (https://docs.astral.sh/uv/)
#   - `docker` is installed and the Docker daemon is running
#   - TEST_DATABASE_URL in backend/.env points at the local Docker container
#     (postgresql+asyncpg://postgres:postgres@localhost:5432/homik_test)
#
# Database setup:
#   Tests run against a local Postgres container defined in docker-compose.yml.
#   This script starts the container automatically if it isn't already running.
#   To start it manually: docker compose up -d db
#   To stop it:           docker compose down
#
# Usage:    chmod +x scripts/run-tests.sh && ./scripts/run-tests.sh
# Shortcut: alias run-tests='./scripts/run-tests.sh'
#
# Output:   docs/test-report.txt

set -uo pipefail  # No -e: test failures are non-zero exits we want to capture

OUTPUT="docs/test-report.txt"
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

echo "Starting local test database..."
docker compose up -d db
until docker compose exec -T db pg_isready -U postgres -q; do sleep 1; done

echo "Test run: $TIMESTAMP" > "$OUTPUT"
(cd "$BACKEND_DIR" && uv run pytest -v 2>&1 | tee -a "../$OUTPUT") || true

echo ""
echo "Done — written to $OUTPUT"
