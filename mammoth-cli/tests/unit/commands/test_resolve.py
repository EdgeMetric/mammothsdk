"""Pure logic behind ``resolve NAME`` and ``dataset find``'s in-project marking."""

from __future__ import annotations

from mammoth_cli.commands.dataset import _tag_scope, elsewhere_note, narrow_to_project
from mammoth_cli.commands.resolve import kinds_note, resolve_matches

_PROJECTS = [
    {"id": 1, "name": "Sales Hub"},
    {"id": 2, "name": "uqa-w29-ren"},
    {"id": 3, "name": None},
]
_DATASETS = [
    {"object_id": 10, "name": "uqa-w29-ren", "project_id": 1},
    {"object_id": 11, "name": "uqa-w29-ren v2", "project_id": 1},
]
_VIEWS = [{"object_id": 20, "name": "Sales view", "project_id": 1}]


def test_a_dataset_name_is_not_read_as_a_project() -> None:
    """The reported mix-up: the name is a dataset in project 1, and project 2 shares it."""
    rows = resolve_matches("UQA-W29-REN", _PROJECTS, {"dataset": _DATASETS})
    exact = [(r["kind"], r["id"], r["project_id"]) for r in rows if r["exact"]]
    assert exact == [("project", 2, 2), ("dataset", 10, 1)]
    assert [r["kind"] for r in rows if not r["exact"]] == ["dataset"]


def test_every_row_names_its_project() -> None:
    rows = resolve_matches("sales", _PROJECTS, {"dataset": [], "view": _VIEWS})
    assert [(r["kind"], r["project_name"]) for r in rows] == [
        ("project", "Sales Hub"),
        ("view", "Sales Hub"),
    ]


def test_home_project_marks_each_row_and_sorts_it_first() -> None:
    rows = resolve_matches("uqa-w29-ren", _PROJECTS, {"dataset": _DATASETS}, home=1)
    exact = [r for r in rows if r["exact"]]
    assert [(r["kind"], r["in_project"]) for r in exact] == [("dataset", True), ("project", False)]


def test_no_home_means_no_in_project_field() -> None:
    rows = resolve_matches("sales", _PROJECTS, {"view": _VIEWS})
    assert all("in_project" not in r for r in rows)


def test_note_says_what_one_exact_name_is() -> None:
    rows = resolve_matches("Sales view", _PROJECTS, {"view": _VIEWS})
    assert kinds_note("Sales view", rows) == "'Sales view' is a view (id 20) in project Sales Hub."


def test_note_lists_the_kinds_when_a_name_is_both() -> None:
    rows = resolve_matches("uqa-w29-ren", _PROJECTS, {"dataset": _DATASETS})
    note = kinds_note("uqa-w29-ren", rows)
    assert "2 things (project, dataset)" in note


def test_note_says_when_nothing_matches() -> None:
    assert "Nothing visible" in kinds_note("zz", resolve_matches("zz", _PROJECTS, {}))


def test_find_marks_matches_in_and_out_of_the_project() -> None:
    tagged = _tag_scope([{"project_id": 1, "id": 5}, {"project_id": 2, "id": 6}], 1)
    assert [(m["id"], m["in_project"]) for m in tagged] == [(5, True), (6, False)]


def test_note_names_the_projects_when_one_kind_repeats() -> None:
    twins = [
        {"object_id": 1, "name": "sales", "project_id": 1},
        {"object_id": 2, "name": "sales", "project_id": 2},
    ]
    rows = resolve_matches("sales", _PROJECTS[:2], {"dataset": twins})
    exact = [r for r in rows if r["kind"] == "dataset"]
    note = kinds_note("sales", exact)
    assert note == "'sales' is 2 datasets, in projects Sales Hub, uqa-w29-ren: ask which."


def test_note_picks_the_one_copy_in_the_current_project() -> None:
    copies = [{"object_id": 13689, "name": "uqa", "project_id": 1}] + [
        {"object_id": 100 + i, "name": "uqa", "project_id": 2} for i in range(35)
    ]
    rows = resolve_matches("uqa", _PROJECTS[:2], {"dataset": copies}, home=1)
    assert kinds_note("uqa", rows) == (
        "'uqa' is a dataset (id 13689) in the current project; 35 more elsewhere."
    )
    elsewhere = resolve_matches("uqa", _PROJECTS[:2], {"dataset": copies}, home=3)
    assert "ask which" in kinds_note("uqa", elsewhere)


def _copies(home: int) -> list[dict[str, object]]:
    rows = resolve_matches(
        "uqa",
        [],
        {
            "dataset": [
                {"object_id": 100 + i, "name": "uqa", "project_id": 1 + i % 2} for i in range(5)
            ]
        },
        home=home,
    )
    return rows


def test_an_exact_match_in_the_project_leaves_only_the_projects_rows() -> None:
    kept, dropped = narrow_to_project(_copies(home=2), lambda r: bool(r["exact"]))
    assert [r["project_id"] for r in kept] == [2, 2]
    assert dropped == 3


def test_no_exact_match_in_the_project_keeps_every_row() -> None:
    rows = _copies(home=3)
    assert narrow_to_project(rows, lambda r: bool(r["exact"])) == (rows, 0)


def test_the_elsewhere_note_names_the_flag_that_lists_them() -> None:
    assert elsewhere_note(0) == ""
    assert '"all_projects": true' in elsewhere_note(36)
