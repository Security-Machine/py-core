from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """A response model for errors.

    Attributes:
        message: The human-readable error message.
        code: The error code that can be used, together with params,
            to reconstruct the message in any language.
        field: The field that caused the error, if any.
        params: The parameters to be used to reconstruct the message.
    """
    message: str
    code: Optional[str]
    field: Optional[str]
    params: Optional[Dict[str, Any]]
