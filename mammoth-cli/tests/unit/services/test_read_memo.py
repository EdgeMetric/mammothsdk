"""Reads made together ahead of a write are answered once, and dropped when the write starts."""

from __future__ import annotations

from mammoth_cli.errors.envelope import CliError
from mammoth_cli.services.read_memo import ReadMemo, prefetch
from mammoth_cli.services.testing import FakeMammothService

_GET = "mammoth.api.dataviews.DataviewsAPI.get"
_EXPORTS = "mammoth.api.exports.ExportsAPI.list"


def test_prefetched_reads_are_answered_without_another_call() -> None:
    service = FakeMammothService(responses={_GET: {"row_count": 5}, _EXPORTS: {"exports": []}})
    prefetch(
        service,
        [
            (_GET, {"dataset_id": 1, "dataview_id": 2, "project_id": 9}),
            (_EXPORTS, {"dataview_id": 2, "dataset_id": 1}),
        ],
    )
    assert len(service.call_log) == 2
    # The project is not part of which record a read returns.
    assert service.call(_GET, dataset_id=1, dataview_id=2, project_id=None) == {"row_count": 5}
    assert service.call(_GET, dataset_id=1, dataview_id=2) == {"row_count": 5}
    assert len(service.call_log) == 2


def test_an_answer_is_a_copy_the_caller_may_change() -> None:
    service = FakeMammothService(responses={_GET: {"metadata": [1]}})
    prefetch(service, [(_GET, {"dataset_id": 1, "dataview_id": 2})])
    service.call(_GET, dataset_id=1, dataview_id=2)["metadata"].append(2)
    assert service.call(_GET, dataset_id=1, dataview_id=2) == {"metadata": [1]}


def test_a_different_record_is_still_read() -> None:
    service = FakeMammothService(responses={_GET: {"row_count": 5}})
    prefetch(service, [(_GET, {"dataset_id": 1, "dataview_id": 2})])
    service.call(_GET, dataset_id=1, dataview_id=3)
    assert len(service.call_log) == 2


def test_a_failed_read_is_returned_and_not_remembered() -> None:
    service = FakeMammothService(responses={_GET: CliError(code="not_found", message="gone")})
    first, second = prefetch(
        service,
        [(_GET, {"dataset_id": 1, "dataview_id": 2}), (_EXPORTS, {"dataview_id": 2})],
    )
    assert isinstance(first, CliError)
    assert second == {}
    try:
        service.call(_GET, dataset_id=1, dataview_id=2)
    except CliError:
        pass
    else:  # pragma: no cover
        raise AssertionError("the failed read must be made again")


def test_a_write_drops_what_was_read_ahead_of_it() -> None:
    service = FakeMammothService(responses={_GET: {"row_count": 5}})
    prefetch(service, [(_GET, {"dataset_id": 1, "dataview_id": 2})])
    service.call_view(2, "filter_rows", dataset_id=1)
    service.responses[_GET] = {"row_count": 3}
    assert service.call(_GET, dataset_id=1, dataview_id=2) == {"row_count": 3}


def test_memo_clear_forgets_everything() -> None:
    memo = ReadMemo()
    memo.store("s", {"a": 1}, "v")
    assert memo.lookup("s", {"a": 1}) == (True, "v")
    memo.clear()
    assert memo.lookup("s", {"a": 1}) == (False, None)
