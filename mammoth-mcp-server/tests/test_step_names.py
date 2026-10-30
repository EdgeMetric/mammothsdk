"""`get_pipeline` names a step's columns as the user sees them, as every other tool takes them."""

from mammoth_mcp_server.step_names import with_display_names

DATE = {"display_name": "date", "internal_name": "column_1", "type": "TEXT"}
FRUIT = {"display_name": "fruit", "internal_name": "column_2", "type": "TEXT"}
CATEGORY = {"display_name": "category", "internal_name": "column_3", "type": "TEXT"}
R_CATEGORY = {"display_name": "r_category", "internal_name": "c_kjeri_1", "type": "TEXT"}
# A join step as Mammoth lists it (a dev server, 28 Oct 2026), cut to what is read.
JOIN = {
    "id": 2800,
    "sequence": 2,
    "params": {
        "JOIN": {
            "ON": [{"LEFT": "column_2", "RIGHT": "column_9"}],
            "TYPE": "LEFT",
            "SELECT": [{"ALIAS": "r_category", "COLUMN": "column_3"}],
            "DATAVIEW_ID": 8645,
        },
        "TASK_KEY": "JOIN",
    },
    "display_info": {
        "analysis": {
            "foreign_columns_used": {
                "column_9": {"display_name": "Fruit name", "internal_name": "column_9"},
                "column_3": {"display_name": "Kind", "internal_name": "column_3"},
            }
        }
    },
    "prev_metadata": [DATE, FRUIT, CATEGORY],
}
FILTER = {
    "id": 2801,
    "sequence": 3,
    "params": {
        "SELECT": {"CONDITION": {"c_kjeri_1": {"EQ": "citrus"}, "column_1": {"NE": "today"}}},
        "TASK_KEY": "SELECT",
    },
    "prev_metadata": [DATE, FRUIT, CATEGORY, R_CATEGORY],
}


def test_a_join_names_its_own_columns_and_the_other_views_by_their_own_names() -> None:
    [step] = with_display_names([JOIN], [DATE, FRUIT, CATEGORY, R_CATEGORY])

    join = step["params"]["JOIN"]
    assert join["ON"] == [{"LEFT": "fruit", "RIGHT": "Fruit name"}]
    # column_3 is "category" here but "Kind" in the other view: the other view's name wins.
    assert join["SELECT"] == [{"ALIAS": "r_category", "COLUMN": "Kind"}]


def test_a_column_an_earlier_step_added_is_named_too_in_keys_and_values() -> None:
    [step] = with_display_names([FILTER], [DATE, FRUIT, CATEGORY, R_CATEGORY])

    assert step["params"]["SELECT"]["CONDITION"] == {
        "r_category": {"EQ": "citrus"},
        "date": {"NE": "today"},
    }


def test_a_column_the_last_step_added_is_named_from_the_view() -> None:
    added = {
        "id": 2802,
        "params": {"ADD_COLUMN": [{"COLUMN": "nc", "INTERNAL_NAME": "column_new"}]},
        "prev_metadata": [DATE],
    }
    view = [DATE, {"display_name": "nc", "internal_name": "column_new", "type": "TEXT"}]

    [step] = with_display_names([added], view)

    assert step["params"]["ADD_COLUMN"] == [{"COLUMN": "nc", "INTERNAL_NAME": "nc"}]


def test_a_value_that_only_looks_like_no_column_is_left_alone() -> None:
    step = {"id": 1, "params": {"SET": [{"VALUE": "column_77"}]}, "prev_metadata": [DATE]}

    [named] = with_display_names([step], [DATE])

    assert named["params"]["SET"] == [{"VALUE": "column_77"}]


def test_the_web_apps_column_lists_are_left_out() -> None:
    [step] = with_display_names([JOIN], [DATE, FRUIT, CATEGORY, R_CATEGORY])

    assert "prev_metadata" not in step
    assert "display_info" not in step
