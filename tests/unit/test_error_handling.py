"""Unit tests for exception classes."""

from __future__ import annotations

from mammoth.exceptions import MammothAPIError, MammothAuthError, MammothColumnError


class TestMammothAPIError:
    def test_basic(self):
        err = MammothAPIError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.status_code is None
        # Default is empty dict, not None
        assert err.response_body == {}

    def test_with_status_code(self):
        err = MammothAPIError("Not found", status_code=404)
        assert err.status_code == 404

    def test_with_response_body(self):
        body = {"detail": "Resource not found"}
        err = MammothAPIError("Not found", status_code=404, response_body=body)
        assert err.response_body == body


class TestMammothAuthError:
    def test_is_api_error(self):
        err = MammothAuthError("Invalid credentials")
        assert isinstance(err, MammothAPIError)

    def test_message(self):
        err = MammothAuthError("Bad auth")
        assert str(err) == "Bad auth"


class TestMammothColumnError:
    def test_message(self):
        err = MammothColumnError("foo", ["bar", "baz"])
        assert "foo" in str(err)
        assert "not found" in str(err)
