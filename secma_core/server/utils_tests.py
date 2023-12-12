import json

import pytest

from secma_core.schemas.errors import ErrorResponse
from secma_core.server.exceptions import HttpError
from secma_core.server.utils import (
    duplicate_app,
    no_app,
    slug_is_valid,
    string_is_valid,
    user_name_is_valid,
)


def test_string_is_valid():
    with pytest.raises(ValueError):
        string_is_valid("")
    assert string_is_valid("a") == "a"
    assert string_is_valid("a" * 255) == "a" * 255
    with pytest.raises(ValueError):
        string_is_valid("a" * 256, 255)


def test_slug_is_valid():
    with pytest.raises(ValueError):
        slug_is_valid("")
    with pytest.raises(ValueError):
        slug_is_valid("a")
    with pytest.raises(ValueError):
        slug_is_valid("a" * 2)
    assert slug_is_valid("a" * 3) == "a" * 3
    assert slug_is_valid("a" * 255) == "a" * 255
    with pytest.raises(ValueError):
        slug_is_valid("a" * 256)
    with pytest.raises(ValueError):
        slug_is_valid("A")
    with pytest.raises(ValueError):
        slug_is_valid("A" * 3)
    with pytest.raises(ValueError):
        slug_is_valid("A" * 255)
    with pytest.raises(ValueError):
        slug_is_valid("A" * 256)
    with pytest.raises(ValueError):
        slug_is_valid("1")
    with pytest.raises(ValueError):
        slug_is_valid("1" * 3)
    with pytest.raises(ValueError):
        slug_is_valid("1" * 255)
    with pytest.raises(ValueError):
        slug_is_valid("1" * 256)
    with pytest.raises(ValueError):
        slug_is_valid("_")
    with pytest.raises(ValueError):
        slug_is_valid("_" * 3)
    with pytest.raises(ValueError):
        slug_is_valid("_" * 255)
    with pytest.raises(ValueError):
        slug_is_valid("_" * 256)
    with pytest.raises(ValueError):
        slug_is_valid("-")
    with pytest.raises(ValueError):
        slug_is_valid("-" * 3)
    with pytest.raises(ValueError):
        slug_is_valid("-" * 255)
    with pytest.raises(ValueError):
        slug_is_valid("-" * 256)
    assert slug_is_valid("a" * 3) == "a" * 3
    assert slug_is_valid("a" * 255) == "a" * 255
    with pytest.raises(ValueError):
        slug_is_valid("a" * 256)


def test_user_name_is_valid_lowercase():
    # Test valid lowercase user name
    assert user_name_is_valid("john") == "john"


def test_user_name_is_valid_uppercase():
    # Test invalid uppercase user name
    with pytest.raises(ValueError):
        user_name_is_valid("John")


def test_user_name_is_valid_special_characters():
    # Test invalid user name with special characters
    with pytest.raises(ValueError):
        user_name_is_valid("john@doe")


def test_user_name_is_valid_empty():
    # Test invalid empty user name
    with pytest.raises(ValueError):
        user_name_is_valid("")


def test_user_name_is_valid_length():
    # Test invalid user name exceeding maximum length
    with pytest.raises(ValueError):
        user_name_is_valid("a" * 256)


def test_no_app_json():
    # Test JSON response for non-existent app
    response = no_app("myapp", mode="json")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    assert json.loads(response.body.decode("utf8")) == {
        "code": "no-app",
        "params": {"appSlug": "myapp"},
        "field": None,
        "message": "No application with a `myapp` slug was found.",
    }


def test_no_app_html():
    # Test HTML response for non-existent app
    response = no_app("myapp", mode="html")
    assert isinstance(response, HttpError)
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    assert isinstance(response.data, ErrorResponse)
    assert response.data.code == "no-app"
    assert response.data.params == {"appSlug": "myapp"}
    assert response.data.field is None
    assert response.data.message == (
        "No application with a `myapp` slug was found."
    )


def test_no_app_invalid_mode():
    # Test invalid mode raises ValueError
    with pytest.raises(ValueError):
        no_app("myapp", mode="invalid")


def test_duplicate_app_json():
    # Test JSON response for duplicate app
    response = duplicate_app("myapp")
    assert response.status_code == 409
    assert response.headers["Content-Type"] == "application/json"
    assert json.loads(response.body.decode("utf8")) == {
        "code": "duplicate-app",
        "params": {"appSlug": "myapp"},
        "field": "slug",
        "message": "An application with a `myapp` slug already exists.",
    }
