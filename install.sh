#!/usr/bin/env bash
set -euo pipefail

# Install lightx2v CLI via pip from ModelTC/LightX2V (LightX2V-Deploy subdirectory).
# Usage: curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh

REPO_URL="${LIGHTX2V_CLI_REPO:-https://github.com/ModelTC/LightX2V.git}"
SUBDIR="${LIGHTX2V_CLI_SUBDIR:-LightX2V-Deploy}"
PIP_SPEC="git+${REPO_URL}#subdirectory=${SUBDIR}"

echo "Installing lightx2v CLI from ${REPO_URL} (${SUBDIR})..."

if command -v pipx >/dev/null 2>&1; then
  pipx install --force "${PIP_SPEC}" || pipx install --force "lightx2v-cli @ ${PIP_SPEC}"
elif command -v pip3 >/dev/null 2>&1; then
  pip3 install --user --upgrade "${PIP_SPEC}"
elif command -v pip >/dev/null 2>&1; then
  pip install --user --upgrade "${PIP_SPEC}"
else
  echo "Error: pip or pipx is required." >&2
  exit 1
fi

if command -v lightx2v >/dev/null 2>&1; then
  echo "Installed: $(lightx2v --help 2>&1 | head -1 || true)"
  echo "Run: lightx2v login"
else
  echo "Install finished. Ensure ~/.local/bin is on your PATH, then run: lightx2v login"
fi
