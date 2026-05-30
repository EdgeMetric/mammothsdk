#!/usr/bin/env bash
# Start the Mammoth MCP server (single unified server).
#
# Usage:
#   ./start.sh              # start
#   ./start.sh stop         # stop
#   ./start.sh status       # check
#   ./start.sh restart      # restart
#
# Logs go to LOG_FILE directory or ./logs/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDDIR="${SCRIPT_DIR}/.pids"

# Read only the scalar vars this script needs from .env.
# Do NOT `source .env` — bash mangles JSON values like CORS_ORIGINS
# by stripping inner quotes.  pydantic-settings reads .env itself.
_read_env() {
    local key="$1"
    [ -f "${SCRIPT_DIR}/.env" ] || return 0
    local line
    line=$(grep -m1 "^${key}=" "${SCRIPT_DIR}/.env" 2>/dev/null) || return 0
    echo "${line#*=}"
}
PORT="${PORT:-$(_read_env PORT)}"
HOST="${HOST:-$(_read_env HOST)}"
LOG_FILE="${LOG_FILE:-$(_read_env LOG_FILE)}"
SERVER_URL="${SERVER_URL:-$(_read_env SERVER_URL)}"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

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

PIDFILE="${PIDDIR}/mammoth-mcp.pid"
LOGFILE="${LOGDIR}/mammoth-mcp.log"

_start() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "  Already running (pid $(cat "$PIDFILE"), port ${PORT})"
        return 0
    fi

    echo "  Starting Mammoth MCP on ${HOST}:${PORT}..."
    PORT="$PORT" \
    MODE=remote \
    ${SERVER_URL:+SERVER_URL="$SERVER_URL"} \
        poetry run uvicorn mammoth_mcp.server:create_app \
            --factory \
            --host "$HOST" \
            --port "$PORT" \
            >> "$LOGFILE" 2>&1 &

    local pid=$!
    echo "$pid" > "$PIDFILE"
    echo "  Started (pid ${pid}, port ${PORT}, log ${LOGFILE})"
}

_stop() {
    if [ ! -f "$PIDFILE" ]; then
        echo "  Not running (no pidfile)"
        return 0
    fi

    local pid
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "  Stopping (pid ${pid})..."
        kill "$pid"
        for _ in $(seq 1 20); do
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.5
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Force-killing (pid ${pid})..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo "  Stopped"
    else
        echo "  Process ${pid} already dead"
    fi
    rm -f "$PIDFILE"
}

_status() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "  RUNNING (pid $(cat "$PIDFILE"), port ${PORT})"
    else
        echo "  STOPPED"
        rm -f "$PIDFILE" 2>/dev/null
    fi
}

case "${1:-start}" in
    start)
        echo "Starting Mammoth MCP server..."
        _start
        echo ""
        echo "  Upstream: http://${HOST}:${PORT}"
        if [ -n "${SERVER_URL:-}" ]; then
            echo "  Public:   ${SERVER_URL}/mcp"
        fi
        ;;
    stop)
        echo "Stopping Mammoth MCP server..."
        _stop
        ;;
    restart)
        echo "Restarting Mammoth MCP server..."
        _stop
        sleep 1
        _start
        ;;
    status)
        echo "Mammoth MCP server status:"
        _status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
