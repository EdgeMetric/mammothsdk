"""A password-protected file says, in every result that shows it, how to unlock it.

The agent saw ``password_protected: true`` on an uploaded PDF and asked the user
for an unlocked copy (FB-15). The flag was in the output; nothing said that the
file's password unlocks it, or which command takes the password.
"""

from __future__ import annotations

from mammoth_cli.runtime.locked_files import with_locked_files


def test_a_locked_file_in_a_file_list_names_the_command_that_unlocks_it() -> None:
    data = {
        "files": [
            {"id": 1323, "name": "targets.pdf", "additional_info": {"password_protected": True}},
            {"id": 1324, "name": "open.pdf", "additional_info": {"password_protected": False}},
        ]
    }

    locked = with_locked_files(data)["locked_files"]

    assert [entry["file_id"] for entry in locked] == [1323]
    assert locked[0]["name"] == "targets.pdf"
    assert "Ask the user for the file's password" in locked[0]["fix"]
    assert "not for an unlocked copy" in locked[0]["fix"]
    assert "mammoth file set-password 1323" in locked[0]["fix"]


def test_a_locked_file_in_a_search_result_is_named_by_its_file_id() -> None:
    # A browse record's ``id`` is the resource row; ``object_id`` is the file.
    record = {
        "id": 13317,
        "object_id": 1323,
        "resource_type": "file_object",
        "name": "targets.pdf",
        "additional_data": {"password_protected": True},
    }

    locked = with_locked_files({"resources": [record]})["locked_files"]

    assert [entry["file_id"] for entry in locked] == [1323]


def test_a_result_with_no_locked_file_is_returned_unchanged() -> None:
    data = {"files": [{"id": 7, "additional_info": {"password_protected": False}}]}

    assert with_locked_files(data) is data
    assert with_locked_files([1, 2]) == [1, 2]
