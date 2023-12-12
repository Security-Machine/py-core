from typing import Annotated, List

from fastapi import APIRouter, Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.permission import Permission
from secma_core.db.models.role import Role
from secma_core.db.selectors import select_perm_by_slug
from secma_core.server.dependencies.role import (
    RoleContextDep,
    RoleIdContextDep,
)
from secma_core.server.permissions.permission import no_perm

from ..constants import e404
from . import router

my_router = APIRouter(
    prefix="/roles/{app_slug}/{tn_slug}/permission",
    tags=["Role Permissions"],
)


class BarePermission(BaseModel):
    """A permission in the reply to the role permissions endpoint."""

    model_config = {"from_attributes": True}

    id: int
    name: str


@my_router.get("/", response_model=List[BarePermission])
async def get_role_permissions(
    context: RoleIdContextDep,
):
    """Get all permissions of an role.

    Note that this will *not* return 404 if the role does not exist.
    """
    results = await context.session.scalars(
        select_perm_by_slug(
            context.app_slug,
            context.tn_slug,
        )
        .join(Permission.roles)
        .filter(Role.id == context.role_id)
    )
    return [BarePermission.model_validate(x) for x in results]


@my_router.put(
    "/{perm_id}", response_model=List[BarePermission], responses={**e404}
)
async def add_permission_to_role(
    context: RoleContextDep,
    perm_id: Annotated[
        int, Path(..., title="The ID of the permission to add.")
    ],
):
    """Add a permission to a role.

    This API cal will return 404 if the permission does not exist or if the
    role does not exist.

    If the permission is already assigned to the role, the API call will
    succeed.
    """
    # Locate requested Permission.
    perm_query = await context.session.execute(
        select_perm_by_slug(context.app_slug, context.tn_slug, id=perm_id)
    )
    try:
        permission = perm_query.scalar_one()
    except NoResultFound:
        return no_perm(perm_id)

    # Create the bond.
    context.role.perms.add(permission)
    await context.session.commit()

    # Return the updated list of permissions.
    return [BarePermission.model_validate(x) for x in context.role.perms]


@my_router.post("/", response_model=List[BarePermission])
async def change_role_permissions(
    context: RoleContextDep,
    data: List[int] = Body(..., title="The new list of permission IDs."),
):
    """Replace role permissions with a new set.

    If any of the permissions does not exist, the API call will fail.
    """
    # Locate requested permissions.
    permissions = await context.session.scalars(
        select_perm_by_slug(
            context.app_slug,
            context.tn_slug,
        ).filter(Permission.id.in_(data))
    )
    missing = set(data) - {x.id for x in permissions}
    if missing:
        return JSONResponse(
            status_code=404,
            content={
                "message": (
                    f"The following permissions do not exist: {missing}"
                ),
            },
        )

    # Replace the permissions.
    context.role.perms = set(permissions)
    await context.session.commit()

    # Return the updated list of permissions.
    return [BarePermission.model_validate(x) for x in permissions]


@my_router.delete("/", response_model=List[BarePermission])
async def remove_permissions_from_role(
    context: RoleContextDep,
    data: List[int] = Body(..., title="The list of permission IDs to remove."),
):
    """Remove permissions from a role.

    If any of the permissions does not exist or is not assigned to the role,
    the API call will fail.
    """
    # Locate requested permissions.
    permissions = await context.session.scalars(
        select_perm_by_slug(
            context.app_slug,
            context.tn_slug,
        )
        .filter(
            Permission.id.in_(data),
        )
        .join(Permission.roles)
        .filter(Role.id == context.role.id)
    )
    missing = set(data) - {x.id for x in permissions}
    if missing:
        return JSONResponse(
            status_code=404,
            content={
                "message": (
                    f"The following permissions were not found with this "
                    f"role: {missing}"
                ),
            },
        )

    # Remove the permissions.
    context.role.perms -= set(permissions)
    await context.session.commit()

    # Return the updated list of permissions.
    return [BarePermission.model_validate(x) for x in context.role.perms]


router.include_router(my_router)
