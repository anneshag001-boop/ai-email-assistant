#!/usr/bin/env bash
set -e

# AI Email Assistant + Cloudflare Quick Tunnel
# Usage: bash deploy/start.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "============================================"
echo " AI Email Assistant + Cloudflare Tunnel"
echo "============================================"
echo ""

# Check for python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.11+ first."
    exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv .venv
fi

# Install deps
echo "[2/4] Installing dependencies..."
.venv/bin/pip install -q -r requirements.txt

# Start server
echo "[3/4] Starting server on http://localhost:8000 ..."
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server
sleep 3

# Check for cloudflared
if ! command -v cloudflared &>/dev/null; then
    echo ""
    echo "cloudflared not found. Install it:"
    echo "  brew install cloudflare/cloudflare/cloudflared"
    echo ""
    echo "Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    echo ""
    echo "Server is running at http://localhost:8000"
    echo "Press Ctrl+C to stop."
    wait $SERVER_PID
    exit 0
fi

# Start tunnel
echo "[4/4] Starting Cloudflare Tunnel..."
echo ""
echo "Public URL will appear below. Share it with anyone."
echo "Press Ctrl+C to stop everything."
echo ""
cloudflared tunnel --url http://localhost:8000

# Cleanup
echo ""
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null
echo "Done."
