#!/usr/bin/env bash
# Moves this copy (option 3, Docker Compose) to the newest official release and restarts it.
# Run it by hand, or weekly from cron (see docs/updates.md). Only published releases are used.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="Self-hosted-MCP/Selfhost-Remote-Mail-MCP"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "This copy has local changes to tracked files; not updating. Undo them or update by hand."
  exit 1
fi
latest=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p')
if ! [[ "$latest" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "No official release found."
  exit 1
fi
current=$(git describe --tags --exact-match 2>/dev/null || echo "none")
if [ "$current" = "$latest" ]; then
  echo "Already on $latest."
  exit 0
fi
git fetch --force --tags origin
git -c advice.detachedHead=false checkout "$latest"
docker compose up -d --build
echo "Updated from $current to $latest."
