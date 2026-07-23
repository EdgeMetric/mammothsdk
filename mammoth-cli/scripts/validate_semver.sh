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

# MAJOR.MINOR.PATCH, each a run of digits, with optional `-prerelease` and
# `+build` metadata. Anchored at both ends so nothing extra may sneak in.
semver='^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'

if ! printf '%s' "$version" | grep -Eq "$semver"; then
    echo "::error::version '$version' is not strict SemVer; it must be MAJOR.MINOR.PATCH[-prerelease][+build]"
    exit 1
fi
