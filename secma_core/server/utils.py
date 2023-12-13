import re
from typing import Literal, Optional

from fastapi.responses import JSONResponse
from pydantic import Field

from secma_core.server.exceptions import HttpError
from secma_core.server.messages import get_err, get_json_err

# Type that indicates the return format for some function.
ErrorMode = Literal["json", "html"]

# Common fields for the models.
SlugField = Field(
    ...,
    title="A string identifier unique among its peers.",
    description=(
        "This needs to be a non-empty, lower case, alpa-numeric string. "
        "When editing a record this field allows you "
        "to change the slug (this will become the new slug) while the "
        "slug in the path is used to identify the record to change."
    ),
)


# Regular expression for the user name validation.
user_regex = re.compile(r"^[a-z0-9\-_]+$")

# Regular expression for the slug validation.
slug_regex = re.compile(r"^[a-z0-9\-_]+$")


def string_is_valid(v: str, max_len: Optional[int] = None) -> str:
    """Validate the string."""
    if len(v) == 0:
        raise ValueError("The string must be non-empty.")
    if max_len is not None and len(v) > max_len:
        raise ValueError(
            f"The string must be less than {max_len} characters in length."
        )
    return v


def slug_is_valid(v: str) -> str:
    """Validate the slug."""
    if not v.islower():
        raise ValueError("The slug must be lowercase.")
    if len(v) < 3:
        raise ValueError(
            "The slug must be at least three characters in length."
        )
    if len(v) > 255:
        raise ValueError("The slug must be less than 255 characters.")
    if not slug_regex.match(v):
        raise ValueError(
            "The slug can include letters, numbers, underscore (_) "
            "and minus (-) characters."
        )
    return v


def user_name_is_valid(v: str) -> str:
    """Validate the unique identifier of the user."""
    if not v.islower():
        raise ValueError("The user name must be lowercase.")
    if not user_regex.match(v):
        raise ValueError(
            "The user name can include letters, numbers, underscore (_) "
            "and minus (-) characters."
        )
    if len(v) == 0:
        raise ValueError("The user name must be non-empty.")
    if len(v) > 255:
        raise ValueError("The user name must be less than 255 characters.")
    return v


def no_app(app_slug: str, mode: ErrorMode = "json"):
    """Return a 404 response for an application that does not exist."""
    error = get_err(
        code="no-app",
        params={"appSlug": app_slug},
    )
    if mode == "json":
        return JSONResponse(
            status_code=404,
            content=error.model_dump(),
        )
    elif mode == "html":
        return HttpError(status_code=404, data=error)
    else:
        raise ValueError(f"Invalid mode: {mode}")


def duplicate_app(app_slug: str):
    """Return a 409 response for an application that already exists."""
    return get_json_err(
        status_code=409,
        message_code="duplicate-app",
        params={"appSlug": app_slug},
        field="slug",
    )


def no_role(role_id: int, mode: ErrorMode = "json"):
    """Return a 404 response for a role that does not exist."""
    error = get_err(
        code="no-role",
        params={"roleId": role_id},
    )
    if mode == "json":
        return JSONResponse(
            status_code=404,
            content=error.model_dump(),
        )
    elif mode == "html":
        return HttpError(status_code=404, data=error)
    else:
        raise ValueError(f"Invalid mode: {mode}")


def no_user(user_id: int, mode: ErrorMode = "json"):
    """Return a 404 response for a user that does not exist."""
    error = get_err(
        code="no-user",
        params={"userId": user_id},
    )
    if mode == "json":
        return JSONResponse(
            status_code=404,
            content=error.model_dump(),
        )
    elif mode == "html":
        return HttpError(status_code=404, data=error)
    else:
        raise ValueError(f"Invalid mode: {mode}")
