#!/usr/bin/env bash
# Strict SemVer validator shared by the three tag-triggered release workflows
# (.github/workflows/sdk-release.yml, cli-release.yml, publish.yml).
#
# Each workflow strips its own tag prefix (sdk-v / cli-v / mcp-v) and passes the
# remaining version string here, so the acceptance rule lives in exactly ONE
# place instead of three inline copies that could drift apart.
#
# A version is accepted only when it is STRICT SemVer:
#     MAJOR.MINOR.PATCH[-prerelease][+build]
# fully anchored. The old release-tag glob `[0-9]*.[0-9]*.[0-9]*` accepted
# non-SemVer such as `1.2.3.4` or `1.2.3abc`; this validator does not, so a
# malformed tag fails fast before any build or publish step runs.
#
# Usage:
#     validate_semver.sh <version>
# Exits 0 when <version> is strict SemVer. Otherwise prints a GitHub Actions
# `::error::` annotation and exits 1.
set -eu

version="${1-}"

# Canonical SemVer 2.0.0 (https://semver.org), as a POSIX ERE:
#   - MAJOR.MINOR.PATCH are non-negative integers with NO leading zeros
#     (`0` or `[1-9][0-9]*`), so `01.2.3` / `1.02.3` / `1.2.03` are rejected.
#   - an optional `-prerelease` is a dot-separated list of non-empty identifiers;
#     a numeric identifier has no leading zero (`1.2.3-01` rejected), and empty
#     identifiers (`1.2.3-alpha..1`, `1.2.3-..`) are rejected.
#   - an optional `+build` is a dot-separated list of non-empty alphanumeric
#     identifiers (leading zeros allowed there, per the spec).
# Anchored at both ends so nothing extra may sneak in.
_num='(0|[1-9][0-9]*)'
_pre_id='(0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)'
_build_id='[0-9a-zA-Z-]+'
semver="^${_num}\.${_num}\.${_num}(-${_pre_id}(\.${_pre_id})*)?(\+${_build_id}(\.${_build_id})*)?\$"

if ! printf '%s' "$version" | grep -Eq "$semver"; then
    echo "::error::version '$version' is not strict SemVer; it must be MAJOR.MINOR.PATCH[-prerelease][+build]"
    exit 1
fi
