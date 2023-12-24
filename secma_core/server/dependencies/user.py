from logging import Logger
from typing import Annotated

from attrs import define
from fastapi import Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.user import User
from secma_core.db.selectors import select_user_by_slug
from secma_core.server.utils import no_user

from .app import AppSlugArg
from .tenant import TenantContext, TenantSlugArg, get_tenant_context


@define
class UserContext(TenantContext):
    """The context for the request with application, tenant and user."""

    user: User


async def get_user_context(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    user_id: int = Path(..., title="The ID of the user."),
) -> UserContext:
    """Get the context for the request with a resolved user.

    This is a dependency that can be used in FastAPI endpoints. It makes a
    database query to resolve the user.

    Args:
        request: The request.
        app_slug: The application slug.
        tn_slug: The tenant slug.
        user_id: The user ID to be located.

    Returns:
        The context.
    """
    session: AsyncSession = request.state.session
    logger: Logger = request.state.logger

    # Locate requested user.
    user_query = await session.execute(
        select_user_by_slug(app_slug, tn_slug, id=user_id)
    )
    try:
        user = user_query.scalar_one()
    except NoResultFound:
        return no_user(user_id)

    # Construct result.
    return UserContext(
        request=request,
        session=session,
        logger=logger,
        app_slug=app_slug,
        tn_slug=tn_slug,
        user=user,
    )


UserContextDep = Annotated[UserContext, Depends(get_tenant_context)]


@define
class UserIdContext(TenantContext):
    """The context for the request with application, tenant and user."""

    user_id: int


async def get_user_id_context(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    user_id: int = Path(..., title="The ID of the user."),
) -> UserIdContext:
    """Get the context for the request with a user id.

    This is a dependency that can be used in FastAPI endpoints. Use it when
    you don't need the user loaded from the database.

    Args:
        request: The request.
        app_slug: The application slug.
        tn_slug: The tenant slug.
        user_id: The user ID to be located.

    Returns:
        The context.
    """
    # Construct result.
    return UserIdContext(
        request=request,
        session=request.state.session,
        app_slug=app_slug,
        tn_slug=tn_slug,
        user_id=user_id,
        logger=request.state.logger,
    )


UserIdContextDep = Annotated[UserIdContext, Depends(get_user_id_context)]
