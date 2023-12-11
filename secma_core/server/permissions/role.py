from typing import List, Union

from fastapi import APIRouter, Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.selectors import select_role_by_id, select_role_by_slug
from secma_core.server.dependencies.app import AppIdArg, AppSlugArg
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.dependencies.tenant import TenantIdArg, TenantSlugArg
from secma_core.server.utils import no_role, string_is_valid

from ..constants import e404, e409
from . import router

my_router = APIRouter(
    prefix="/roles/{app_slug}/{tn_slug}",
    tags=["Roles"],
)


class RoleData(BaseModel):
    """The data associated with an role.

    This model is used for creating and editing roles.
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
    def role_is_valid(cls, v):
        """Validate the slug."""
        return string_is_valid(v, 255)


def duplicate_role(role_name: str):
    """Return a 409 response for a role that already exists."""
    return JSONResponse(
        status_code=409,
        content={
            "message": (
                f"A role with a `{role_name}` role name already exists "
                "withing this tenant."
            ),
        },
    )


@my_router.get("/", response_model=List[int])
async def get_roles(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
):
    """Get a list of all unique roles IDs in a tenant."""
    results = await context.session.scalars(
        select_role_by_slug(app_slug, tn_slug).options(load_only(Role.id))
    )
    return [x.id for x in results]


@my_router.put("/", responses={**e409}, response_model=RoleData)
async def create_role(
    context: ContextDep,
    app_id: AppIdArg,
    tn_id: TenantIdArg,
    data: RoleData = Body(),
) -> Union[RoleData, JSONResponse]:
    """Create a new role in a tenant."""

    # Check if the role name already exists.
    if await context.session.scalar(
        select_role_by_id(app_id, tn_id, name=data.name)
    ):
        return duplicate_role(data.name)

    # Create the new role.
    new_rec = Role(name=data.name, tenant_id=tn_id)
    context.session.add(new_rec)
    await context.session.commit()
    return RoleData.model_validate(new_rec)


@my_router.get("/{role_id}", responses={**e404}, response_model=RoleData)
async def get_role(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    role_id: int = Path(..., title="The ID of the role to retrieve."),
):
    """Get information about a specific role."""
    query = await context.session.execute(
        select_role_by_slug(app_slug, tn_slug, id=role_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_role(role_id)
    return RoleData.model_validate(result)


@my_router.post(
    "/{role_id}", responses={**e404, **e409}, response_model=RoleData
)
async def edit_role(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    role_id: int = Path(..., title="The ID of the role to edit."),
    data: RoleData = Body(),
):
    """Edit an existing role."""
    # Locate requested record.
    query = await context.session.execute(
        select_role_by_slug(app_slug, tn_slug, id=role_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_role(role_id)

    # Check if the role-name already exists.
    if await context.session.scalar(
        select_role_by_slug(app_slug, tn_slug, name=data.name).filter(
            Role.id != result.id
        )
    ):
        return duplicate_role(data.name)

    # Update the record.
    result.name = data.name
    await context.session.commit()

    return RoleData.model_validate(result)


@my_router.delete("/{role_id}", responses={**e404}, response_model=RoleData)
async def delete_role(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    role_id: int = Path(..., title="The ID of the role to delete."),
):
    """Delete an existing role."""
    # Locate requested record.
    query = await context.session.execute(
        select_role_by_slug(app_slug, tn_slug, id=role_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_role(role_id)

    # Delete the record.
    await context.session.delete(result)
    await context.session.commit()
    return RoleData.model_validate(result)


router.include_router(my_router)
