#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Publish Job Hunter Bot to GitHub"
echo "================================="
echo

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not logged in."
  echo "Run: gh auth login"
  exit 1
fi

REPO_NAME="${1:-job-hunter-bot}"
VISIBILITY="${2:-private}"

git branch -M main
gh repo create "$REPO_NAME" --source=. --remote=origin --push "--$VISIBILITY"

echo
echo "Done! Open in Cursor:"
echo "  1. Cursor -> File -> Clone from GitHub"
echo "  2. Select $REPO_NAME"
echo
gh repo view --json url -q .url
