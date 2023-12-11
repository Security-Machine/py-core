from typing import Annotated

from attrs import define
from fastapi import Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.selectors import select_role_by_slug
from secma_core.server.utils import no_role

from .app import AppSlugArg
from .tenant import TenantContext, TenantSlugArg, get_tenant_context


@define
class RoleContext(TenantContext):
    """The context for the request with application, tenant and role."""

    role: Role


async def get_role_context(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    role_id: int = Path(..., title="The ID of the role."),
) -> RoleContext:
    """Get the context for the request with a resolved role.

    This is a dependency that can be used in FastAPI endpoints. It makes a
    database query to resolve the role.

    Args:
        request: The request.
        app_slug: The application slug.
        tn_slug: The tenant slug.
        role_id: The role ID to be located.

    Returns:
        The context.
    """
    session: AsyncSession = request.state.session

    # Locate requested role.
    role_query = await session.execute(
        select_role_by_slug(app_slug, tn_slug, id=role_id)
    )
    try:
        role = role_query.scalar_one()
    except NoResultFound:
        return no_role(role_id)

    # Construct result.
    return RoleContext(
        request=request,
        session=session,
        settings=request.state.settings,
        app_slug=app_slug,
        tn_slug=tn_slug,
        role=role,
        logger=request.state.logger,
    )


RoleContextDep = Annotated[RoleContext, Depends(get_tenant_context)]


@define
class RoleIdContext(TenantContext):
    """The context for the request with application, tenant and role."""

    role_id: int


async def get_role_id_context(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    role_id: int = Path(..., title="The ID of the role."),
) -> RoleIdContext:
    """Get the context for the request with a role id.

    This is a dependency that can be used in FastAPI endpoints. Use it when
    you don't need the role loaded from the database.

    Args:
        request: The request.
        app_slug: The application slug.
        tn_slug: The tenant slug.
        role_id: The role ID to be located.

    Returns:
        The context.
    """
    # Construct result.
    return RoleIdContext(
        request=request,
        session=request.state.session,
        settings=request.state.settings,
        app_slug=app_slug,
        tn_slug=tn_slug,
        role_id=role_id,
        logger=request.state.logger,
    )


RoleIdContextDep = Annotated[RoleIdContext, Depends(get_role_id_context)]
