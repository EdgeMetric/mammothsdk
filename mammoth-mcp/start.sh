#!/usr/bin/env bash
# Start all three MCP server profiles using the current Python/venv.
#
# Port assignment uses environment variables:
#   TRANSFORMATIONS_PORT (default: PORT+0, e.g. 9000)
#   IMPORT_PORT          (default: PORT+1, e.g. 9001)
#   ADMIN_PORT           (default: PORT+2, e.g. 9002)
#
# Falls back to PORT from .env (default 8000) as the base.
#
# Usage:
#   ./start.sh              # start all 3 profiles
#   ./start.sh stop         # stop all 3 profiles
#   ./start.sh status       # check which profiles are running
#   ./start.sh restart      # restart all 3 profiles
#
# Logs go to LOG_FILE directory or ./logs/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDDIR="${SCRIPT_DIR}/.pids"

# Load .env if it exists (for PORT, LOG_LEVEL, etc.)
if [ -f "${SCRIPT_DIR}/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "${SCRIPT_DIR}/.env"
    set +a
fi

# Base port from PORT env var (same as settings.py default)
BASE_PORT="${PORT:-8000}"

# Per-profile ports: explicit env var or base + offset
TRANSFORMATIONS_PORT="${TRANSFORMATIONS_PORT:-$BASE_PORT}"
IMPORT_PORT="${IMPORT_PORT:-$((BASE_PORT + 1))}"
ADMIN_PORT="${ADMIN_PORT:-$((BASE_PORT + 2))}"

declare -A PORTS=(
    [transformations]="$TRANSFORMATIONS_PORT"
    [import]="$IMPORT_PORT"
    [admin]="$ADMIN_PORT"
)

# Log directory — use LOG_FILE dir if set, else try /var/log, else ./logs
if [ -n "${LOG_FILE:-}" ]; then
    LOGDIR="$(dirname "$LOG_FILE")"
elif [ -w "/var/log/mammoth-mcp" ] 2>/dev/null || mkdir -p "/var/log/mammoth-mcp" 2>/dev/null; then
    LOGDIR="/var/log/mammoth-mcp"
else
    LOGDIR="${SCRIPT_DIR}/logs"
fi
mkdir -p "$LOGDIR"
mkdir -p "$PIDDIR"

HOST="${HOST:-0.0.0.0}"

_start() {
    local profile="$1"
    local port="${PORTS[$profile]}"
    local pidfile="${PIDDIR}/${profile}.pid"
    local logfile="${LOGDIR}/${profile}.log"

    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "  ${profile} already running (pid $(cat "$pidfile"), port ${port})"
        return 0
    fi

    echo "  Starting ${profile} on ${HOST}:${port}..."
    MCP_PROFILE="$profile" \
    PORT="$port" \
    MODE=remote \
        python -m uvicorn mammoth_mcp.server:create_app \
            --factory \
            --host "$HOST" \
            --port "$port" \
            >> "$logfile" 2>&1 &

    local pid=$!
    echo "$pid" > "$pidfile"
    echo "  ${profile} started (pid ${pid}, port ${port}, log ${logfile})"
}

_stop() {
    local profile="$1"
    local pidfile="${PIDDIR}/${profile}.pid"

    if [ ! -f "$pidfile" ]; then
        echo "  ${profile}: not running (no pidfile)"
        return 0
    fi

    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
        echo "  Stopping ${profile} (pid ${pid})..."
        kill "$pid"
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Force-killing ${profile} (pid ${pid})..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo "  ${profile} stopped"
    else
        echo "  ${profile}: process ${pid} already dead"
    fi
    rm -f "$pidfile"
}

_status() {
    local profile="$1"
    local port="${PORTS[$profile]}"
    local pidfile="${PIDDIR}/${profile}.pid"

    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "  ${profile}: RUNNING (pid $(cat "$pidfile"), port ${port})"
    else
        echo "  ${profile}: STOPPED"
        rm -f "$pidfile" 2>/dev/null
    fi
}

case "${1:-start}" in
    start)
        echo "Starting Mammoth MCP servers..."
        for profile in transformations import admin; do
            _start "$profile"
        done
        echo ""
        echo "Upstream targets:"
        echo "  transformations → http://${HOST}:${TRANSFORMATIONS_PORT}"
        echo "  import          → http://${HOST}:${IMPORT_PORT}"
        echo "  admin           → http://${HOST}:${ADMIN_PORT}"
        ;;
    stop)
        echo "Stopping Mammoth MCP servers..."
        for profile in transformations import admin; do
            _stop "$profile"
        done
        ;;
    restart)
        echo "Restarting Mammoth MCP servers..."
        for profile in transformations import admin; do
            _stop "$profile"
        done
        sleep 1
        for profile in transformations import admin; do
            _start "$profile"
        done
        ;;
    status)
        echo "Mammoth MCP server status:"
        for profile in transformations import admin; do
            _status "$profile"
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
