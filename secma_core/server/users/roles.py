from typing import Annotated, List

from fastapi import APIRouter, Body
from fastapi.params import Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.models.user import User
from secma_core.db.selectors import select_role_by_slug
from secma_core.server.dependencies.user import (
    UserContextDep,
    UserIdContextDep,
)
from secma_core.server.utils import no_role

from ..constants import e404
from . import router

my_router = APIRouter(
    prefix="/{user_id}/roles",
    tags=["User Roles"],
)


class BareRole(BaseModel):
    """A role in the reply to the user roles endpoint."""

    model_config = {"from_attributes": True}

    id: int
    name: str


@my_router.get("/", response_model=List[BareRole])
async def get_user_roles(
    context: UserIdContextDep,
):
    """Get all roles of an user.

    Note that this will *not* return 404 if the user does not exist.
    """
    results = await context.session.scalars(
        select_role_by_slug(
            context.app_slug,
            context.tn_slug,
        )
        .join(Role.users)
        .filter(User.id == context.user_id)
    )
    return [BareRole.model_validate(x) for x in results]


@my_router.put("/{role_id}", response_model=List[BareRole], responses={**e404})
async def add_role_to_user(
    context: UserContextDep,
    role_id: Annotated[int, Path(..., title="The ID of the role to add.")],
):
    """Add a role to a user.

    This API cal will return 404 if the role does not exist or if the user
    does not exist.

    If the role is already assigned to the user, the API call will succeed.
    """
    # Locate requested role.
    role_query = await context.session.execute(
        select_role_by_slug(context.app_slug, context.tn_slug, id=role_id)
    )
    try:
        role = role_query.scalar_one()
    except NoResultFound:
        return no_role(role_id)

    # Create the bond.
    context.user.roles.add(role)
    await context.session.commit()

    # Return the updated list of roles.
    return [BareRole.model_validate(x) for x in context.user.roles]


@my_router.post("/", response_model=List[BareRole])
async def change_user_roles(
    context: UserContextDep,
    data: List[int] = Body(..., title="The new list of role IDs."),
):
    """Replace user roles with a new set.

    If any of the roles does not exist, the API call will fail.
    """
    # Locate requested roles.
    roles = await context.session.scalars(
        select_role_by_slug(
            context.app_slug,
            context.tn_slug,
        ).filter(Role.id.in_(data))
    )
    missing = set(data) - {x.id for x in roles}
    if missing:
        return JSONResponse(
            status_code=404,
            content={
                "message": (f"The following roles do not exist: {missing}"),
            },
        )

    # Replace the roles.
    context.user.roles = set(roles)
    await context.session.commit()

    # Return the updated list of roles.
    return [BareRole.model_validate(x) for x in roles]


@my_router.delete("/", response_model=List[BareRole])
async def remove_roles_from_user(
    context: UserContextDep,
    data: List[int] = Body(..., title="The list of role IDs to remove."),
):
    """Remove roles from a user.

    If any of the roles does not exist or is not assigned to the user,
    the API call will fail.
    """
    # Locate requested roles.
    roles = await context.session.scalars(
        select_role_by_slug(
            context.app_slug,
            context.tn_slug,
        )
        .filter(
            Role.id.in_(data),
        )
        .join(Role.users)
        .filter(User.id == context.user.id)
    )
    missing = set(data) - {x.id for x in roles}
    if missing:
        return JSONResponse(
            status_code=404,
            content={
                "message": (
                    f"The following roles were not found with this "
                    f"user: {missing}"
                ),
            },
        )

    # Remove the roles.
    context.user.roles -= set(roles)
    await context.session.commit()

    # Return the updated list of roles.
    return [BareRole.model_validate(x) for x in context.user.roles]


router.include_router(my_router)
