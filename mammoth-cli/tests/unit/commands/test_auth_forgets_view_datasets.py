"""``auth login`` and ``auth logout`` clear the remembered view -> dataset answers."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from mammoth_cli.context import credentials, profiles
from mammoth_cli.runtime import view_dataset_cache
from mammoth_cli.services.testing import FakeMammothService
from mammoth_cli.testing import make_runner

_TOKEN = "mm_" + "A" * 43


def _seed() -> Path:
    """A remembered answer on disk, as an earlier command would have left it."""
    directory = view_dataset_cache.cache_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "view-datasets-0123456789abcdef.json"
    path.write_text('{"entries": {"1:290": 424}}', encoding="utf-8")
    return path


def test_login_forgets_remembered_view_datasets(
    isolated_cli_config: Path, fake_service: FakeMammothService, tmp_path: Path
) -> None:
    kept = _seed()
    doc = tmp_path / "login.json"
    doc.write_text(json.dumps({"api_token": _TOKEN, "server_prefix": "release"}), encoding="utf-8")
    os.chmod(doc, stat.S_IRUSR | stat.S_IWUSR)
    result = make_runner().invoke(
        ["auth", "login", "--input", str(doc), "--storage", "file", "--output", "json"], env={}
    )
    assert result.exit_code == 0, result.stderr
    assert not kept.exists()


def test_logout_forgets_remembered_view_datasets(
    isolated_cli_config: Path, fake_service: FakeMammothService
) -> None:
    profiles.save_profile(profiles.ProfileRecord(name="default", workspace_id=4))
    credentials.store_credentials("default", storage="file", api_token=_TOKEN)
    profiles.set_selected("default")
    kept = _seed()
    result = make_runner().invoke(["auth", "logout", "--yes", "--output", "json", "--no-input"])
    assert result.exit_code == 0, result.stderr
    assert not kept.exists()
