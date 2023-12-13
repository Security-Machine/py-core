import json

import pytest
from fastapi.responses import JSONResponse

from .messages import get_err, get_json_err


def test_get_err_existing_code():
    # Test getting error response for an existing code
    error = get_err("no-role")
    assert error.code == "no-role"
    assert error.field is None
    assert error.params is None
    assert error.message == (
        "No role with a `{roleId}` ID was found withing this tenant."
    )


def test_get_err_existing_code_with_params():
    # Test getting error response for an existing code with params
    error = get_err("no-role", params={"roleId": "name"})
    assert error.code == "no-role"
    assert error.field is None
    assert error.params == {"roleId": "name"}
    assert error.message == (
        "No role with a `name` ID was found withing this tenant."
    )


def test_get_err_nonexistent_code():
    # Test getting error response for a nonexistent code
    with pytest.raises(KeyError):
        get_err("nonexistent-code")


def test_get_err_existing_code_with_field():
    # Test getting error response for an existing code with field
    error = get_err("no-role", field="name")
    assert error.code == "no-role"
    assert error.field == "name"
    assert error.params is None
    assert error.message == (
        "No role with a `{roleId}` ID was found withing this tenant."
    )


def test_get_json_err_existing_code():
    # Test getting JSON error response for an existing code
    response = get_json_err(400, "no-app")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert json.loads(response.body.decode("utf8")) == {
        "code": "no-app",
        "field": None,
        "params": None,
        "message": "No application with a `{appSlug}` slug was found.",
    }


def test_get_json_err_existing_code_with_params():
    # Test getting JSON error response for an existing code with params
    response = get_json_err(400, "no-app", {"appSlug": "myapp"})
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert json.loads(response.body.decode("utf8")) == {
        "code": "no-app",
        "field": None,
        "params": {"appSlug": "myapp"},
        "message": "No application with a `myapp` slug was found.",
    }


def test_get_json_err_nonexistent_code():
    # Test getting JSON error response for a nonexistent code
    with pytest.raises(KeyError):
        get_json_err(500, "nonexistent-code")


def test_get_json_err_existing_code_with_field():
    # Test getting JSON error response for an existing code with field
    response = get_json_err(400, "no-app", field="name")
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert json.loads(response.body.decode("utf8")) == {
        "code": "no-app",
        "field": "name",
        "params": None,
        "message": "No application with a `{appSlug}` slug was found.",
    }
