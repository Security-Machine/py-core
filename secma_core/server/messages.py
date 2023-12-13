from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse

from secma_core.schemas.errors import ErrorResponse

messages = {
    "duplicate-app": (
        "An application with a `{appSlug}` slug already exists."
    ),
    "no-role": "No role with a `{roleId}` ID was found withing this tenant.",
    "no-app": "No application with a `{appSlug}` slug was found.",
    "no-user": "No user with a `{userId}` ID was found withing this tenant.",
    "invalid-credentials": (
        "Could not validate credentials (trace ID: {uniqueId})."
    ),
    "no-permission": "Not enough permissions (trace ID: {uniqueId}).",
}


def get_err(
    code: str,
    params: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
) -> ErrorResponse:
    """Get an error model from a code.

    Args:
        code (str): The error code.
        field (Optional[str], optional): The field that caused the error.
            Defaults to None.

    Returns:
        ErrorResponse: The error response model. The message is populated
            by using the code to look up the message in the messages dict.

    Raises:
        KeyError: If the code is not found in the messages dict.
    """
    message = messages[code]
    if params:
        message = message.format(**params)
    return ErrorResponse(
        message=message, code=code, field=field, params=params
    )


def get_json_err(
    status_code: int,
    message_code: str,
    params: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
) -> JSONResponse:
    """Creates a json response from an error code.

    Args:
        status_code: The status code of the response.
        message_code: The error code.
        field: The field that caused the error.
            Defaults to None.
        params: The parameters to be used in the error message.
    """
    return JSONResponse(
        status_code=status_code,
        content=get_err(
            code=message_code, params=params, field=field
        ).model_dump(),
    )
