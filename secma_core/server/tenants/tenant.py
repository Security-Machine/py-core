from typing import List, Union

from fastapi import Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.application import Application
from secma_core.db.models.tenant import Tenant
from secma_core.server.dependencies.app import AppIdArg, AppSlugArg
from secma_core.server.dependencies.auth import CoreSecurity
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.utils import SlugField, slug_is_valid

from ..constants import e404, e409
from . import router


class TenantData(BaseModel):
    """The data for an tenant.

    This model is used for creating and editing tenants.
    """

    model_config = {"from_attributes": True}

    slug: str = SlugField

    @field_validator("slug")
    def slug_is_valid(cls, v):
        """Validate the slug."""
        return slug_is_valid(v)


def no_tenant(tn_slug: str):
    """Return a 404 response for a tenant that does not exist."""
    return JSONResponse(
        status_code=404,
        content={
            "message": (
                f"No tenant with a `{tn_slug}` slug was found "
                "withing this application."
            ),
        },
    )


def duplicate_tenant(tn_slug: str):
    """Return a 409 response for a tenant that already exists."""
    return JSONResponse(
        status_code=409,
        content={
            "message": (
                f"A tenant with a `{tn_slug}` slug already exists "
                "withing this application."
            ),
        },
    )


@router.get(
    "/", response_model=List[str], dependencies=[CoreSecurity("tenants:r")]
)
async def get_tenants(context: ContextDep, app_slug: AppSlugArg):
    """Get a list of all unique tenant slugs available in this application."""
    results = await context.session.scalars(
        select(Tenant)
        .options(load_only(Tenant.slug))
        .join(Tenant.application)
        .filter(Application.slug == app_slug)
    )
    return [x.slug for x in results]


@router.put(
    "/",
    responses={**e409},
    response_model=TenantData,
    dependencies=[CoreSecurity("tenant:c")],
)
async def create_tenant(
    context: ContextDep,
    app_id: AppIdArg,
    data: TenantData = Body(),
) -> Union[TenantData, JSONResponse]:
    """Create a new tenant."""

    # Check if the slug already exists.
    if await context.session.scalar(
        select(Tenant).filter(
            Tenant.slug == data.slug,
            Tenant.application_id == app_id,
        )
    ):
        return duplicate_tenant(data.slug)

    # Create the new tenant.
    new_app = Tenant(slug=data.slug, application_id=app_id)
    context.session.add(new_app)
    await context.session.commit()
    return TenantData.model_validate(new_app)


@router.get(
    "/{tn_slug}",
    responses={**e404},
    response_model=TenantData,
    dependencies=[CoreSecurity("tenant:r")],
)
async def get_tenant(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: str = Path(..., title="The name of the tenant to retrieve."),
):
    """Get information about a specific tenant."""
    query = await context.session.execute(
        select(Tenant)
        .filter(
            Tenant.slug == tn_slug,
        )
        .join(Tenant.application)
        .filter(Tenant.application.has(slug=app_slug))
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_tenant(tn_slug)
    return TenantData.model_validate(result)


@router.post(
    "/{tn_slug}",
    responses={**e404, **e409},
    response_model=TenantData,
    dependencies=[CoreSecurity("tenant:u")],
)
async def edit_tenant(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: str,
    data: TenantData = Body(),
):
    """Edit an existing tenant."""
    # Locate requested record.
    query = await context.session.execute(
        select(Tenant)
        .filter(
            Tenant.slug == tn_slug,
        )
        .join(Tenant.application)
        .filter(Tenant.application.has(slug=app_slug))
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_tenant(tn_slug)

    # Check if the slug already exists.
    if await context.session.scalar(
        select(Tenant).filter(
            Tenant.slug == data.slug,
            Tenant.id != result.id,
        )
    ):
        return duplicate_tenant(data.slug)

    # Update the record.
    result.slug = data.slug
    await context.session.commit()

    return TenantData.model_validate(result)


@router.delete(
    "/{tn_slug}",
    responses={**e404},
    response_model=TenantData,
    dependencies=[CoreSecurity("tenant:d")],
)
async def delete_tenant(
    context: ContextDep, app_slug: AppSlugArg, tn_slug: str
):
    """Delete an existing tenant."""
    # Locate requested record.
    query = await context.session.execute(
        select(Tenant)
        .filter(
            Tenant.slug == tn_slug,
        )
        .join(Tenant.application)
        .filter(Tenant.application.has(slug=app_slug))
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_tenant(tn_slug)

    # Delete the record.
    await context.session.delete(result)
    await context.session.commit()
    return TenantData.model_validate(result)
