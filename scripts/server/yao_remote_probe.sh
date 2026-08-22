#!/usr/bin/env bash
set -euo pipefail

echo "user=$(whoami)"
echo "host=$(hostname)"
echo "pwd=$PWD"
echo "home=$HOME"
command -v labctl >/dev/null 2>&1 && labctl status || true
command -v sinfo >/dev/null 2>&1 && sinfo || true
command -v squeue >/dev/null 2>&1 && squeue -u "$USER" || true
command -v uv >/dev/null 2>&1 && uv --version || true

