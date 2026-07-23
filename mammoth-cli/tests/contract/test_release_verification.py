"""Contract test: documented Sigstore verification commands are constrained.

A keyless ``cosign verify-blob`` that omits certificate-identity and OIDC-issuer
constraints accepts *any* valid Sigstore certificate, so it does not prove the
artifact came from the expected EdgeMetric/mammothsdk release workflow. Every
place that documents the verify command must pin both constraints.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_CLI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _CLI_ROOT.parent

# The release workflow lives at the repository root; the CLI installation guide
# (which documents the verified install flow) lives under the CLI package.
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "cli-release.yml"
_INSTALL_DOCS = _CLI_ROOT / "docs" / "installation.md"


@pytest.mark.parametrize("path", [_WORKFLOW, _INSTALL_DOCS])
def test_verify_blob_pins_identity_and_issuer(path: Path) -> None:
    assert path.exists(), f"expected documentation file is missing: {path}"
    text = path.read_text(encoding="utf-8")

    assert "verify-blob" in text, f"{path} documents no cosign verify-blob command"
    assert "--certificate-identity" in text, (
        f"{path} verify-blob command omits --certificate-identity(-regexp); "
        "any valid Sigstore certificate would pass"
    )
    assert "--certificate-oidc-issuer" in text, (
        f"{path} verify-blob command omits --certificate-oidc-issuer; "
        "any valid Sigstore certificate would pass"
    )
