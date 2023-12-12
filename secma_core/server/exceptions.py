from typing import Dict, Optional

from fastapi.responses import JSONResponse

from secma_core.schemas.errors import ErrorResponse


class HttpError(Exception):
    """Exception raised for errors that will generate a HTTP response.

    Use this instead of the standard HTTPException class to avoid
    wrapping the error in a `details` member.

    Attributes:
        data: the error response data
        status_code: the HTTP status code returned
        headers: the HTTP headers to send to the client
    """

    def __init__(
        self,
        status_code: int,
        data: ErrorResponse,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.data = data
        self.status_code = status_code
        self.headers = {
            **(headers if headers else {}),
            "Content-Type": "application/json",
        }

    @property
    def message(self) -> str:
        """Return the error message."""
        return self.data.message

    @property
    def detail(self) -> ErrorResponse:
        """Return the message body."""
        return self.data

    def to_response(self) -> JSONResponse:
        """Return a JSON response from this exception."""
        return JSONResponse(
            content=self.data.model_dump(),
            status_code=self.status_code,
            headers=self.headers,
        )
