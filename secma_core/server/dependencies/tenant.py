from typing import Annotated

from attrs import define
from fastapi import Depends, Path, Request
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.application import Application
from secma_core.db.models.tenant import Tenant
from secma_core.server.utils import no_app

from .app import AppSlugArg
from .context import Context


async def get_tenant_id(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: str = Path(
        ...,
        title="The slug of the tenant.",
        description=(
            "This needs to be a non-empty, lower case, alpa-numeric string."
        ),
    ),
) -> int:
    """Get the tenant from path.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        app_slug: The application provided in the url.
        tn_slug: The tenant provided in the url.

    Returns:
        The tenant ID.
    """

    query = await request.state.session.execute(
        select(Tenant)
        .options(load_only(Tenant.id))
        .filter(Tenant.slug == tn_slug)
        .join(Tenant.application)
        .filter(Application.slug == app_slug)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        raise no_app(app_slug, mode="html")

    return result.id


TenantIdArg = Annotated[int, Depends(get_tenant_id)]


async def get_tenant_slug(
    # request: Request,
    tn_slug: str = Path(
        ...,
        title="The slug of the tenant.",
        description=(
            "This needs to be a non-empty, lower case, alpa-numeric string."
        ),
    ),
) -> str:
    """Get the tenant slug from path.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        tn_slug: The value provided in the url.

    Returns:
        The application slug.
    """
    return tn_slug


TenantSlugArg = Annotated[str, Depends(get_tenant_slug)]


@define
class TenantContext(Context):
    """The context for the request with application and tenant."""

    app_slug: str
    tn_slug: str


def get_tenant_context(
    request: Request,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
) -> TenantContext:
    """Get the tenant context for the request (includes the application).

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        request: The request.
        app_slug: The application slug.
        tn_slug: The tenant slug.

    Returns:
        The context.
    """
    return TenantContext(
        request=request,
        session=request.state.session,
        app_slug=app_slug,
        tn_slug=tn_slug,
        logger=request.state.logger,
    )


TenantContextDep = Annotated[TenantContext, Depends(get_tenant_context)]
