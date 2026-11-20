#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Day 6: ML Lifecycle & Pipelines — JupyterLab Launcher"
echo "============================================================"

# 1. Verify Docker is installed and running
if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] Docker is not installed. Please install Docker Desktop first."
  echo "        See DOCKER_SETUP.md for step-by-step instructions."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] Docker daemon is not running. Start Docker Desktop and try again."
  exit 1
fi

# 2. Initialize .env from .env.example if missing
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[INFO] Created .env from .env.example"
fi

# Read defaults from .env if present
JUPYTER_PORT=8888
JUPYTER_TOKEN="day6-training"
if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
fi

# 3. Verify notebooks folder exists
if [ ! -d "../notebooks" ]; then
  echo "[ERROR] Expected ../notebooks directory next to docker-jupyterlab/."
  exit 1
fi

echo "[INFO] Building and starting JupyterLab container..."
docker compose up -d --build

echo ""
echo "[READY] JupyterLab is starting up!"
echo "        Open in your browser:"
echo "        http://localhost:${JUPYTER_PORT}/lab?token=${JUPYTER_TOKEN}"
echo ""
echo "Useful commands:"
echo "  View logs : docker compose logs -f"
echo "  Stop lab  : docker compose down"
echo "============================================================"
