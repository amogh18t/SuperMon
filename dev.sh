#!/bin/bash

# SuperMon Developer Mode Script (Zero Docker, SQLite Engine, Instant Startup)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND="${1:-start}"

case "$COMMAND" in
    start|"")
        echo -e "\033[0;34m[DEV MODE]\033[0m Starting SuperMon with SQLite (No Docker required)..."
        python3 "$DIR/supermon.py" dev
        ;;
    stop)
        "$DIR/stop_all.sh"
        ;;
    restart)
        "$DIR/stop_all.sh"
        sleep 1
        python3 "$DIR/supermon.py" dev
        ;;
    status)
        python3 "$DIR/supermon.py" status
        ;;
    logs)
        TARGET="${2:-all}"
        mkdir -p "$DIR/logs" "$DIR/logs/mcp"
        case "$TARGET" in
            backend)
                tail -f "$DIR/logs/backend.log"
                ;;
            frontend)
                tail -f "$DIR/logs/frontend.log"
                ;;
            mcp)
                tail -f "$DIR/logs/mcp"/*.log
                ;;
            *)
                tail -f "$DIR/logs"/*.log "$DIR/logs/mcp"/*.log 2>/dev/null
                ;;
        esac
        ;;
    *)
        echo "Usage: ./dev.sh [start|stop|restart|status|logs [backend|frontend|mcp]]"
        ;;

esac
