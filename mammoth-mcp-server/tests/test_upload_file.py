"""`upload_file` returns once Mammoth has read the file, with the dataset it made.

Seen live: it returned after 1.5 s with only job ids, so a file still being
read, one waiting on the user and one ready all looked the same.
"""

from typing import Any
from unittest.mock import patch

from mammoth_mcp_server.consts import DatasetStatus, FileStatus, ResourceTypes

from .helpers import WORKSPACE, a_fake_api, as_caller, call_tool

PROJECT, FILE, DATASET, VIEW = 3, 12, 21, 9
PROJECT_PATH = f"/workspaces/{WORKSPACE}/projects/{PROJECT}"
FILES = f"{PROJECT_PATH}/files"
RESOURCES = f"{PROJECT_PATH}/resources"
VIEWS = f"{PROJECT_PATH}/datasets/{DATASET}/dataviews"
IDS = {"workspace_id": WORKSPACE, "project_id": PROJECT}
UPLOAD = {**IDS, "file_name": "sales.csv", "content": "name,amount\na,1\n"}
# What the upload job returns: one job per file (a dev server, 28 Oct 2026).
PER_FILE = {"errors": {}, "job_ids": [{"job_id": 42, "file_object_id": FILE, "resource_id": 99}]}
SHORT_CALL = patch("mammoth_mcp_server.deadline.TOOL_CALL_SECONDS", 0.05)
QUICK_POLL = patch("mammoth_mcp_server.upload_wait.UPLOAD_POLL_SECONDS", 0.01)


def done(response: dict[str, Any]) -> dict[str, Any]:
    return {"job": {"id": 0, "status": "success", "response": response}}


def an_item(kind: str, object_id: int, status: str) -> dict[str, Any]:
    # Made after the upload was sent, as everything the upload made is.
    return {
        "resource_type": kind,
        "object_id": object_id,
        "name": "sales.csv",
        "status": status,
        "created_at": "2099-01-01T00:00:00Z",
        "object_properties": {},
    }


READ = [
    an_item(ResourceTypes.FILE, FILE, FileStatus.PROCESSED),
    an_item(ResourceTypes.DATASET, DATASET, DatasetStatus.READY),
]
STILL_READING = [
    an_item(ResourceTypes.FILE, FILE, FileStatus.PROCESSING),
]


def an_upload(
    api: Any, per_file_job: dict[str, Any] | None = None, started: dict[str, Any] = PER_FILE
) -> None:
    api.answer("POST", FILES, {"job": {"id": 41}})
    api.answer("GET", "/jobs/41", done(started))
    api.answer("GET", "/jobs/42", per_file_job or done({}))
    api.answer("GET", VIEWS, {"dataviews": [{"id": VIEW}]})


class TestUploadingText:
    def test_it_waits_for_the_file_and_names_the_dataset_and_its_view(self) -> None:
        with a_fake_api() as api, as_caller():
            an_upload(api)
            api.answer("GET", RESOURCES, {"resources": READ})
            report = call_tool("upload_file", **UPLOAD)

        assert api.sent("GET", "/jobs/42"), "it did not wait for the file's own job"
        assert report["status"] == "done"
        [dataset] = [item for item in report["files"] if item["kind"] == "dataset"]
        assert dataset["dataset_id"] == DATASET
        assert dataset["view_id"] == VIEW
        assert "job_ids" not in report

    def test_a_dataset_still_being_made_is_waited_for(self) -> None:
        with a_fake_api() as api, as_caller(), QUICK_POLL:
            an_upload(api)
            api.answer("GET", RESOURCES, {"resources": STILL_READING})
            api.answer("GET", RESOURCES, {"resources": READ})
            report = call_tool("upload_file", **UPLOAD)

        assert len(api.sent("GET", RESOURCES)) == 2
        assert report["status"] == "done"

    def test_a_file_refused_by_mammoth_is_reported(self) -> None:
        with a_fake_api() as api, as_caller():
            an_upload(api, started={**PER_FILE, "errors": {"sales.csv": "empty"}})
            api.answer("GET", RESOURCES, {"resources": READ})
            report = call_tool("upload_file", **UPLOAD)

        assert report["rejected"] == {"sales.csv": "empty"}

    def test_a_file_still_read_when_the_call_ends_says_so_and_names_its_job(self) -> None:
        running = {"job": {"id": 42, "status": "processing", "response": None}}
        with a_fake_api() as api, as_caller(), SHORT_CALL:
            an_upload(api, per_file_job=running)
            api.answer("GET", RESOURCES, {"resources": STILL_READING})
            report = call_tool("upload_file", **UPLOAD)

        assert report["status"] == "processing"
        assert report["job_ids"] == [42]
        assert "get_job" in report["next_step"]
