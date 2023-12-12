"""The Flask application.

This is the module that should be imported when you want to add something
to the application.
"""
import pkgutil
from typing import Any, Optional

from fastapi import FastAPI

from secma_core.schemas.errors import ErrorResponse

app: Optional[FastAPI] = None


def create_app(lifespan: Any, set_global: bool = False) -> FastAPI:
    """Create the FastAPI application.

    Args:
        set_global (bool): If True, set the global ``app`` variable to the
            created application. Defaults to False.
    """
    global app

    # Read the description from the Markdown file.
    description = pkgutil.get_data(__name__, "app.md")
    assert description is not None

    # Create a new Flask application.
    result = FastAPI(
        title="Secure Machine Core API",
        version="1.0.0",
        description=description.decode("utf-8"),
        responses={
            500: {
                "model": ErrorResponse,
                "description": "Internal server error.",
            }
        },
        lifespan=lifespan,
    )

    if set_global:
        app = result
    return result
