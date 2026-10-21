#!/bin/bash

# SuperMon SDLC Automation Platform - Stop All Services Script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\033[0;34m[INFO]\033[0m Stopping all SuperMon services..."

# 1. Run graceful python stop
python3 "$DIR/supermon.py" stop 2>/dev/null

# 2. Port and process cleanup (free port 8000 and 3000 if lingering)
for port in 8000 3000; do
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "\033[1;33m[CLEANUP]\033[0m Freeing port $port (PID: $pids)..."
        kill -9 $pids 2>/dev/null
    fi
done

# 3. Clean up stale PID files
rm -f "$DIR/.run"/*.pid "$DIR"/*.pid 2>/dev/null

echo -e "\033[0;32m[SUCCESS]\033[0m All SuperMon servers, MCP bridges, and background processes are closed."

