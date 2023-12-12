from fastapi import __version__ as fastapi_version
from pydantic import BaseModel, Field
from pydantic import __version__ as pydantic_version

from secma_core.__version__ import __version__
from secma_core.server.dependencies.auth import CoreSecurity

from . import router


class ApiVersionReply(BaseModel):
    """API version reply."""

    api: str = Field(
        ..., description="The version of the API as a SemVer string."
    )
    fastapi: str = Field(..., description="The version of the FastAPI engine.")
    pydantic: str = Field(
        ..., description="The version of the pydantic library."
    )


@router.get(
    "/version",
    response_model=ApiVersionReply,
    dependencies=[CoreSecurity("version:r")],
)
async def api_version() -> ApiVersionReply:
    """Return the API version."""
    return ApiVersionReply(
        api=__version__,
        fastapi=fastapi_version,
        pydantic=pydantic_version,
    )
