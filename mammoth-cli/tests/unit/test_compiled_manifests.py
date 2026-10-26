"""The committed ``spec/manifests/compiled`` JSON must match the YAML it is built from."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from mammoth_cli.manifest import loader


@pytest.fixture(autouse=True)
def _fresh() -> Iterator[None]:
    loader.clear_cache()
    yield
    loader.clear_cache()


@pytest.mark.parametrize(
    "name",
    [
        loader.COMPILED_COMMANDS,
        loader.COMPILED_OPERATIONS,
        loader.COMPILED_SDK_METHODS,
        loader.COMPILED_OUTPUT_SCHEMAS,
    ],
)
def test_compiled_manifest_matches_the_yaml(name: str) -> None:
    compiled = json.loads((loader.COMPILED_DIR / f"{name}.json").read_text(encoding="utf-8"))
    assert (
        compiled == loader.parse_yaml_manifests()[name]
    ), "compiled manifests are stale: run `python mammoth-cli/scripts/compile_manifests.py`"


def test_compile_manifests_output_is_what_is_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    committed = {p.name: p.read_text(encoding="utf-8") for p in loader.COMPILED_DIR.glob("*.json")}
    monkeypatch.setattr(loader, "COMPILED_DIR", tmp_path)
    written = loader.compile_manifests()
    assert {p.name: p.read_text(encoding="utf-8") for p in written} == committed


def test_loaders_read_compiled_json_not_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_yaml(path: Path) -> None:
        raise AssertionError(f"parsed YAML: {path}")

    monkeypatch.setattr(loader, "_read_yaml", no_yaml)
    assert any(r["command_id"] == "view.list" for r in loader.load_commands())
    assert loader.load_operations() and loader.load_sdk_methods()


def test_missing_compiled_json_falls_back_to_yaml_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "COMPILED_DIR", tmp_path / "none")
    monkeypatch.setattr(loader, "cache_dir", lambda: tmp_path / "cache")
    assert any(r["command_id"] == "view.list" for r in loader.load_commands())
    assert loader.load_operations() and loader.load_sdk_methods()
    assert not (tmp_path / "none").exists() and not (tmp_path / "cache").exists()


def test_legacy_caches_are_removed_once_and_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(loader, "cache_dir", lambda: cache)
    old = [
        "commands-0123abcd-" + "0" * 24 + ".json",
        "commands-" + "1" * 24 + ".json",
        "openapi-operations-0123abcd-" + "2" * 24 + ".json",
        "sdk-methods-0123abcd-" + "3" * 24 + ".json",
        "commands-0123abcd-" + "4" * 24 + ".jsonabc.tmp",
    ]
    keep = ["keyring-backend.json", "update-check.json"]
    for name in old + keep:
        (cache / name).write_text("[]")

    loader.load_commands()
    assert sorted(p.name for p in cache.iterdir() if not p.name.startswith(".")) == sorted(keep)

    # Once: a file that appears after the marker is left alone.
    later = cache / ("commands-0123abcd-" + "5" * 24 + ".json")
    later.write_text("[]")
    loader.clear_cache()
    loader.load_commands()
    assert later.exists()


def test_a_missing_cache_dir_is_not_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "cache_dir", lambda: tmp_path / "cache")
    loader.load_commands()
    assert not (tmp_path / "cache").exists()
