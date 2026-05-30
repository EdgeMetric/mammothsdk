"""HTTP bridge server for the Mammoth SDK.

Receives JSON-RPC-style requests from browser artifacts (or any HTTP
client), dispatches to the Python SDK server-side, and returns results
with CORS headers.  This bypasses browser CORS restrictions without
requiring any changes to the Mammoth API itself.

Usage::

    # Install bridge dependencies
    poetry install --with bridge   # or: pip install -e ".[bridge]"

    # Configure credentials in bridge/.env (see README.md)

    # Run
    python bridge/main.py
    python bridge/main.py --port 5555 --base-url https://app.mammoth.io/api/v2
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from flask import Flask, Response, jsonify, request
except ImportError:
    sys.exit(
        "Flask is required for the bridge server.\n"
        "Install with: poetry install --with bridge  (or: pip install flask python-dotenv)"
    )

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit(
        "python-dotenv is required for the bridge server.\n"
        "Install with: poetry install --with bridge  (or: pip install flask python-dotenv)"
    )

from mammoth import MammothClient
from mammoth.exceptions import (
    MammothAuthError,
    MammothColumnError,
    MammothError,
    MammothJobFailedError,
    MammothJobTimeoutError,
    MammothTransformError,
)

from dispatch import Dispatcher

# ── App setup ─────────────────────────────────────────────────

app = Flask(__name__)
dispatcher: Dispatcher | None = None


def _init_dispatcher(
    api_key: str,
    api_secret: str,
    workspace_id: int,
    base_url: str = "https://app.mammoth.io/api/v2",
) -> Dispatcher:
    client = MammothClient(
        api_key=api_key,
        api_secret=api_secret,
        workspace_id=workspace_id,
        base_url=base_url,
    )
    return Dispatcher(client)


# ── CORS ──────────────────────────────────────────────────────

@app.after_request
def _cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ── Routes ────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    assert dispatcher is not None
    ok = dispatcher.client.test_connection()
    status = 200 if ok else 503
    return jsonify({"ok": ok}), status


@app.route("/methods", methods=["GET"])
def methods() -> tuple[Response, int]:
    assert dispatcher is not None
    return jsonify(dispatcher.list_methods()), 200


@app.route("/rpc", methods=["POST", "OPTIONS"])
def rpc() -> tuple[Response, int]:
    if request.method == "OPTIONS":
        return jsonify({}), 204

    assert dispatcher is not None
    body = request.get_json(silent=True)
    if not body or "method" not in body:
        return jsonify({"ok": False, "error": "BadRequest",
                        "message": "JSON body with 'method' key required"}), 400

    method = body["method"]
    view_id = body.get("view_id")
    args = body.get("args", {})

    try:
        result = dispatcher.dispatch(method, view_id=view_id, args=args)
        return jsonify({"ok": True, "result": result}), 200
    except MammothAuthError as e:
        return jsonify({"ok": False, "error": "MammothAuthError",
                        "message": str(e)}), 401
    except (MammothColumnError, MammothTransformError) as e:
        return jsonify({"ok": False, "error": type(e).__name__,
                        "message": str(e)}), 400
    except MammothJobTimeoutError as e:
        return jsonify({"ok": False, "error": "MammothJobTimeoutError",
                        "message": str(e)}), 504
    except MammothJobFailedError as e:
        return jsonify({"ok": False, "error": "MammothJobFailedError",
                        "message": str(e)}), 502
    except MammothError as e:
        return jsonify({"ok": False, "error": type(e).__name__,
                        "message": str(e)}), 500
    except (ValueError, TypeError, AttributeError) as e:
        return jsonify({"ok": False, "error": type(e).__name__,
                        "message": str(e)}), 400


# ── CLI entry point ───────────────────────────────────────────

def main() -> None:
    # Load .env from the bridge directory
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)

    parser = argparse.ArgumentParser(description="Mammoth SDK HTTP bridge")
    parser.add_argument("--port", type=int, default=int(os.getenv("BRIDGE_PORT", "5555")))
    parser.add_argument("--host", default=os.getenv("BRIDGE_HOST", "127.0.0.1"))
    parser.add_argument("--api-key", default=os.getenv("MAMMOTH_API_KEY"))
    parser.add_argument("--api-secret", default=os.getenv("MAMMOTH_API_SECRET"))
    parser.add_argument("--workspace-id", type=int, default=None)
    parser.add_argument("--base-url", default=os.getenv("MAMMOTH_BASE_URL",
                                                         "https://app.mammoth.io/api/v2"))
    cli_args = parser.parse_args()

    api_key = cli_args.api_key
    api_secret = cli_args.api_secret
    workspace_id = cli_args.workspace_id or (
        int(os.getenv("MAMMOTH_WORKSPACE_ID", "0")) or None
    )

    if not api_key or not api_secret or not workspace_id:
        sys.exit(
            "Missing credentials. Set MAMMOTH_API_KEY, MAMMOTH_API_SECRET, "
            "and MAMMOTH_WORKSPACE_ID in bridge/.env or pass via CLI args."
        )

    global dispatcher
    dispatcher = _init_dispatcher(
        api_key=api_key,
        api_secret=api_secret,
        workspace_id=workspace_id,
        base_url=cli_args.base_url,
    )

    print(f"Mammoth bridge listening on http://{cli_args.host}:{cli_args.port}")
    print(f"  Workspace: {workspace_id}")
    print(f"  Base URL:  {cli_args.base_url}")
    app.run(host=cli_args.host, port=cli_args.port, debug=False)


if __name__ == "__main__":
    main()
