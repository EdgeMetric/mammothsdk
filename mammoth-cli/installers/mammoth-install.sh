#!/bin/sh
# Mammoth CLI installer for Linux and macOS (POSIX sh).
#
# Installs the `mammoth` CLI with uv (pinned) and, by default, the bundled
# agent skill for Codex, Claude Code, and Cursor at user scope. It never
# requires administrator privileges, never disables TLS verification, and never
# modifies a certificate store. It honors standard HTTP proxy variables.
#
# Usage:
#   mammoth-install.sh [--version X.Y.Z] [--cli-only | --skills-only]
#                      [--local[=DIR]] [--no-modify-path] [--noninteractive]
#                      [--help]
#
# The versioned release embeds an exact --version default. A checksum- and
# Sigstore-verified flow is documented in the release notes; this script is the
# convenience path.
#
# --local builds the CLI and its mammoth-io SDK dependency from this source
# checkout and installs ONLINE: the two monorepo wheels resolve from a local
# wheelhouse (--find-links) while every other runtime dependency (typer, rich,
# platformdirs, ...) still resolves normally from PyPI. This is NOT an offline
# installer -- a clean machine has no cached copies of those third-party
# packages, so a plain --no-index install cannot resolve them. DIR defaults to
# the mammoth-cli directory this script ships in.

set -eu

UV_PINNED_VERSION="0.11.30"
CLI_PACKAGE="mammoth-cli"
INSTALL_CLI=1
INSTALL_SKILLS=1
MODIFY_PATH=1
NONINTERACTIVE=0
LOCAL_SOURCE=0
LOCAL_DIR=""
VERSION="__CLI_VERSION__" # replaced at release build; empty/placeholder = latest published

log() { printf '%s\n' "mammoth-install: $1" >&2; }
die() { log "error: $1"; exit 1; }

usage() {
    sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --version) shift; [ $# -gt 0 ] || die "--version needs a value"; VERSION="$1" ;;
        --version=*) VERSION="${1#*=}" ;;
        --cli-only) INSTALL_SKILLS=0 ;;
        --skills-only) INSTALL_CLI=0 ;;
        --local) LOCAL_SOURCE=1 ;;
        --local=*) LOCAL_SOURCE=1; LOCAL_DIR="${1#*=}" ;;
        --no-modify-path) MODIFY_PATH=0 ;;
        --noninteractive|--yes|-y) NONINTERACTIVE=1 ;;
        --help|-h) usage ;;
        *) die "unknown option: $1 (try --help)" ;;
    esac
    shift
done

[ "$INSTALL_CLI" -eq 1 ] || [ "$INSTALL_SKILLS" -eq 1 ] || die "--cli-only and --skills-only are mutually exclusive"

# --- Platform detection -----------------------------------------------------
detect_platform() {
    os="$(uname -s)"
    arch="$(uname -m)"
    case "$os" in
        Linux) platform_os="linux" ;;
        Darwin) platform_os="macos" ;;
        MINGW*|MSYS*|CYGWIN*)
            # git-bash/MSYS2/Cygwin on Windows report a *_NT uname here. This is
            # not an unsupported platform, just the wrong installer: defer to
            # the native PowerShell installer instead of aborting. Exit 0 (not
            # a failure) so a CI job or script that runs this by mistake on
            # Windows does not fail — it is simply the wrong entry point.
            log "Windows detected via '$os' (git-bash/MSYS/Cygwin)."
            log "Use the PowerShell installer instead: mammoth-install.ps1"
            exit 0
            ;;
        *) die "unsupported OS '$os'. Install manually: uv tool install $CLI_PACKAGE" ;;
    esac
    case "$arch" in
        x86_64|amd64) platform_arch="x86_64" ;;
        aarch64|arm64) platform_arch="aarch64" ;;
        *) die "unsupported architecture '$arch'. Install manually: uv tool install $CLI_PACKAGE" ;;
    esac
    if [ "$platform_os" = "linux" ] && ! ldd --version 2>&1 | grep -qi glibc; then
        log "warning: non-glibc libc detected; continuing, but glibc is the supported target"
    fi
}

# --- uv acquisition ---------------------------------------------------------
ensure_uv() {
    if command -v uv >/dev/null 2>&1; then
        UV_BIN="$(command -v uv)"
        log "using existing uv at $UV_BIN"
        return
    fi
    # Install the pinned uv into an installer-owned location; never replace a
    # user's uv. Astral's official installer verifies its own download.
    log "uv not found; installing pinned uv $UV_PINNED_VERSION into an installer-owned dir"
    UV_INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mammoth-cli/uv-$UV_PINNED_VERSION"
    mkdir -p "$UV_INSTALL_DIR"
    if command -v curl >/dev/null 2>&1; then
        UV_INSTALL_SCRIPT="$(curl -fsSL "https://astral.sh/uv/$UV_PINNED_VERSION/install.sh")" \
            || die "could not download uv (offline or proxy failure). Install uv manually, then re-run."
    elif command -v wget >/dev/null 2>&1; then
        UV_INSTALL_SCRIPT="$(wget -qO- "https://astral.sh/uv/$UV_PINNED_VERSION/install.sh")" \
            || die "could not download uv. Install uv manually, then re-run."
    else
        die "neither curl nor wget is available; install uv manually, then re-run"
    fi
    UV_UNMANAGED_INSTALL="$UV_INSTALL_DIR" NO_MODIFY_PATH=1 sh -c "$UV_INSTALL_SCRIPT" \
        || die "uv installation failed"
    UV_BIN="$UV_INSTALL_DIR/uv"
    [ -x "$UV_BIN" ] || UV_BIN="$UV_INSTALL_DIR/bin/uv"
    [ -x "$UV_BIN" ] || die "uv was not installed where expected"
}

# --- CLI install ------------------------------------------------------------
resolve_bin_dir() {
    BIN_DIR="$("$UV_BIN" tool dir --bin 2>/dev/null || true)"
    [ -n "$BIN_DIR" ] || BIN_DIR="$HOME/.local/bin"
}

install_cli() {
    if [ -n "$VERSION" ] && [ "$VERSION" != "__CLI_VERSION__" ]; then
        spec="$CLI_PACKAGE==$VERSION"
    else
        spec="$CLI_PACKAGE"
    fi
    log "installing $spec with uv"
    "$UV_BIN" tool install --force "$spec" || die "uv tool install failed for $spec"
    resolve_bin_dir
}

# Build the CLI and its mammoth-io SDK dependency from this source checkout,
# then install ONLINE: --find-links makes the two just-built wheels resolvable
# while uv still consults PyPI (the default index) for every other runtime
# dependency. There is no offline mode here -- a clean machine has none of
# typer/rich/platformdirs/etc. cached, so --no-index would leave them
# unresolvable.
install_cli_local() {
    script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
    cli_dir="${LOCAL_DIR:-$(CDPATH= cd -- "$script_dir/.." && pwd)}"
    [ -f "$cli_dir/pyproject.toml" ] || die "no CLI project at '$cli_dir' (pass --local=DIR)"
    # The mammoth-io SDK is the repository root that contains the CLI directory.
    sdk_dir="$(CDPATH= cd -- "$cli_dir/.." && pwd)"
    [ -f "$sdk_dir/pyproject.toml" ] || die "no mammoth-io SDK project at '$sdk_dir'"

    wheelhouse="$(mktemp -d "${TMPDIR:-/tmp}/mammoth-wheelhouse.XXXXXX")" \
        || die "could not create a temporary wheelhouse"
    log "building mammoth-io and $CLI_PACKAGE wheels from $sdk_dir"
    "$UV_BIN" build --wheel --out-dir "$wheelhouse" "$sdk_dir" \
        || die "failed to build the mammoth-io SDK wheel"
    "$UV_BIN" build --wheel --out-dir "$wheelhouse" "$cli_dir" \
        || die "failed to build the $CLI_PACKAGE wheel"
    log "installing $CLI_PACKAGE online (mammoth-io/$CLI_PACKAGE from the local wheelhouse, other deps from PyPI)"
    # --find-links adds the local wheels as an extra source so mammoth-io and
    # mammoth-cli resolve to what was just built here, in addition to (not
    # instead of) the default index -- deliberately no --no-index, so every
    # other runtime dependency still resolves normally from PyPI.
    # Pick the first matching wheel for each distribution with a strictly POSIX
    # shell glob, rather than a depth-limited `find` (that flag is a GNU/BSD
    # extension, not part of POSIX find). An unmatched glob expands to the
    # literal pattern in sh, so guard each candidate with `[ -f ]`; if nothing
    # matches, cli_wheel/sdk_wheel stay empty and the guard below fires.
    cli_wheel=""
    for candidate in "$wheelhouse"/mammoth_cli-*.whl; do
        [ -f "$candidate" ] || continue
        cli_wheel="$candidate"
        break
    done
    sdk_wheel=""
    for candidate in "$wheelhouse"/mammoth_io-*.whl; do
        [ -f "$candidate" ] || continue
        sdk_wheel="$candidate"
        break
    done
    [ -n "$cli_wheel" ] && [ -n "$sdk_wheel" ] || die "built wheel artifacts were not found"
    # Install the exact CLI artifact and explicitly inject the exact SDK
    # artifact. PyPI remains enabled only for their third-party dependencies;
    # it cannot substitute either monorepo distribution.
    "$UV_BIN" tool install --force "$cli_wheel" --with "$sdk_wheel" \
        || die "uv tool install failed from the local wheelhouse"
    resolve_bin_dir
    tool_root="$("$UV_BIN" tool dir 2>/dev/null)"
    tool_python="$tool_root/$CLI_PACKAGE/bin/python"
    [ -x "$tool_python" ] || die "could not locate the installed CLI environment"
    "$tool_python" - "$cli_wheel" "$sdk_wheel" <<'PY' || die "installed local distributions failed verification"
import importlib.metadata as md
import json
import pathlib
import re
import sys
import urllib.parse

def wheel_version(path):
    match = re.match(r"[^-]+-([^-]+)-", pathlib.Path(path).name)
    if not match:
        raise SystemExit(f"unrecognized wheel name: {path}")
    return match.group(1)

expected = {"mammoth-cli": wheel_version(sys.argv[1]), "mammoth-io": wheel_version(sys.argv[2])}
for distribution, version in expected.items():
    installed = md.distribution(distribution)
    actual = installed.version
    if actual != version:
        raise SystemExit(f"{distribution}: installed {actual}, expected local wheel {version}")
    direct_url = json.loads(installed.read_text("direct_url.json") or "{}")
    expected_wheel = pathlib.Path(sys.argv[1 if distribution == "mammoth-cli" else 2]).resolve()
    actual_url = direct_url.get("url", "")
    parsed = urllib.parse.urlparse(actual_url)
    if parsed.scheme != "file":
        raise SystemExit(f"{distribution}: installed source is not a file URL: {actual_url!r}")
    actual_wheel = pathlib.Path(urllib.parse.unquote(parsed.path)).resolve()
    if actual_wheel != expected_wheel:
        raise SystemExit(f"{distribution}: installed source is not {expected_wheel}: {actual_url!r}")
PY
    rm -rf "$wheelhouse"
}

# --- PATH handling ----------------------------------------------------------
modify_path() {
    [ "$MODIFY_PATH" -eq 1 ] || { log "PATH unchanged (--no-modify-path). Add $BIN_DIR to PATH."; return; }
    case ":$PATH:" in
        *":$BIN_DIR:"*) log "PATH already contains $BIN_DIR"; return ;;
    esac
    line="export PATH=\"$BIN_DIR:\$PATH\""
    for rc in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
        [ -e "$rc" ] || continue
        grep -Fq "$line" "$rc" 2>/dev/null && continue
        printf '\n# Added by mammoth-install\n%s\n' "$line" >> "$rc"
        log "added $BIN_DIR to PATH in $rc"
    done
    log "open a new shell, or run: $line"
}

install_skills() {
    exe="$BIN_DIR/mammoth"
    [ -x "$exe" ] || exe="mammoth"
    # A failed skill install must fail the installer: do NOT downgrade it to a
    # warning. Use an explicit if/else so the failure branch calls die (exit 1)
    # rather than a `&& ... || ...` chain that would swallow the nonzero status.
    if "$exe" skill install --output json --no-input >/dev/null 2>&1; then
        log "installed the agent skill for all agents (user scope)"
    else
        die "skill install did not complete; run 'mammoth skill install' manually"
    fi
}

main() {
    if [ "$INSTALL_CLI" -eq 1 ]; then
        detect_platform
        ensure_uv
        if [ "$LOCAL_SOURCE" -eq 1 ]; then
            install_cli_local
        else
            install_cli
        fi
        modify_path
    else
        BIN_DIR="$($(command -v uv || echo uv) tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
    fi
    [ "$INSTALL_SKILLS" -eq 1 ] && install_skills
    log "done"
}

main
