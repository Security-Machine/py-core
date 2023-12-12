from typing import List, Union

from fastapi import APIRouter, Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.permission import Permission
from secma_core.db.selectors import select_perm_by_id, select_perm_by_slug
from secma_core.server.dependencies.app import AppIdArg, AppSlugArg
from secma_core.server.dependencies.auth import CoreSecurity
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.dependencies.tenant import TenantIdArg, TenantSlugArg
from secma_core.server.utils import string_is_valid

from ..constants import e404, e409
from . import router

my_router = APIRouter(
    prefix="/perm/{app_slug}/{tn_slug}",
    tags=["Permissions"],
)


class PermData(BaseModel):
    """The data associated with an permission.

    This model is used for creating and editing perms.
    """

    model_config = {"from_attributes": True}

    name: str = Field(
        ...,
        title="A string unique inside parent tenant.",
        description=(
            "This needs to be a non-empty string shorter than 255 characters."
        ),
    )

    @field_validator("name")
    def name_is_valid(cls, v):
        """Validate the name."""
        return string_is_valid(v, 255)


def no_perm(perm_id: int):
    """Return a 404 response for a permissions that does not exist."""
    return JSONResponse(
        status_code=404,
        content={
            "message": (
                f"No permission with a `{perm_id}` ID was found "
                "withing this tenant."
            ),
        },
    )


def duplicate_perm(perm_name: str):
    """Return a 409 response for a permission that already exists."""
    return JSONResponse(
        status_code=409,
        content={
            "message": (
                f"A permission with a `{perm_name}` name already exists "
                "withing this tenant."
            ),
        },
    )


@my_router.get(
    "/", response_model=List[int], dependencies=[CoreSecurity("perms:r")]
)
async def get_permissions(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
):
    """Get a list of all unique permission IDs in a tenant."""
    results = await context.session.scalars(
        select_perm_by_slug(app_slug, tn_slug).options(
            load_only(Permission.id)
        )
    )
    return [x.id for x in results]


@my_router.put(
    "/",
    responses={**e409},
    response_model=PermData,
    dependencies=[CoreSecurity("perm:c")],
)
async def create_permission(
    context: ContextDep,
    app_id: AppIdArg,
    tn_id: TenantIdArg,
    data: PermData = Body(),
) -> Union[PermData, JSONResponse]:
    """Create a new permission in a tenant."""

    # Check if the permission name already exists.
    if await context.session.scalar(
        select_perm_by_id(app_id, tn_id, name=data.name)
    ):
        return duplicate_perm(data.name)

    # Create the new permission.
    new_rec = Permission(name=data.name, tenant_id=tn_id)
    context.session.add(new_rec)
    await context.session.commit()
    return PermData.model_validate(new_rec)


@my_router.get(
    "/{perm_id}",
    responses={**e404},
    response_model=PermData,
    dependencies=[CoreSecurity("perm:r")],
)
async def get_permission(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    perm_id: int = Path(..., title="The ID of the permission to retrieve."),
):
    """Get information about a specific permission."""
    query = await context.session.execute(
        select_perm_by_slug(app_slug, tn_slug, id=perm_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_perm(perm_id)
    return PermData.model_validate(result)


@my_router.post(
    "/{perm_id}",
    responses={**e404, **e409},
    response_model=PermData,
    dependencies=[CoreSecurity("perm:u")],
)
async def edit_permission(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    perm_id: int = Path(..., title="The ID of the permission to edit."),
    data: PermData = Body(),
):
    """Edit an existing permission."""
    # Locate requested record.
    query = await context.session.execute(
        select_perm_by_slug(app_slug, tn_slug, id=perm_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_perm(perm_id)

    # Check if the permission-name already exists.
    if await context.session.scalar(
        select_perm_by_slug(app_slug, tn_slug, name=data.name).filter(
            Permission.id != result.id,
        )
    ):
        return duplicate_perm(data.name)

    # Update the record.
    result.name = data.name
    await context.session.commit()

    return PermData.model_validate(result)


@my_router.delete(
    "/{perm_id}",
    responses={**e404},
    response_model=PermData,
    dependencies=[CoreSecurity("perm:d")],
)
async def delete_permission(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    perm_id: int = Path(..., title="The ID of the permission to delete."),
):
    """Delete an existing permission."""
    # Locate requested record.
    query = await context.session.execute(
        select_perm_by_slug(app_slug, tn_slug, id=perm_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_perm(perm_id)

    # Delete the record.
    await context.session.delete(result)
    await context.session.commit()
    return PermData.model_validate(result)


router.include_router(my_router)
