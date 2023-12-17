from logging import Logger
from typing import Annotated

from attrs import define
from fastapi import Depends, Request
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ..settings import Settings


@define
class Context:
    """The context for the request.

    Attributes:
        request (Request): The original request.
        session (AsyncSession): The database session.
        settings (Settings): The loaded settings.
        logger (Logger): The logger to use.
    """

    request: Request
    session: AsyncSession
    logger: Logger

    @property
    def pwd_context(self) -> CryptContext:
        """The password context."""
        return self.request.app.extra["pwd_context"]

    @property
    def engine(self) -> AsyncEngine:
        """The database engine."""
        return self.request.app.extra["engine"]

    @property
    def settings(self) -> Settings:
        """The database engine."""
        return self.request.app.extra["settings"]


def get_context(request: Request) -> Context:
    """Get the context for the request.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        request: The request.

    Returns:
        The context.
    """
    return Context(
        request=request,
        session=request.state.session,
        logger=request.state.logger,
    )


ContextDep = Annotated[Context, Depends(get_context)]
