from typing import List, Optional, Tuple, Union, cast

from fastapi import APIRouter, Body, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.application import Application
from secma_core.db.models.role import Role
from secma_core.db.models.tenant import Tenant
from secma_core.db.models.user import User
from secma_core.db.selectors import select_user_by_slug
from secma_core.server.dependencies.app import AppSlugArg
from secma_core.server.dependencies.auth import AuthUserDep, CoreSecurity
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.dependencies.tenant import TenantIdArg, TenantSlugArg
from secma_core.server.utils import no_user, user_name_is_valid

from ..constants import e404, e409
from . import router

my_router = APIRouter(
    tags=["User Management"],
)


class UserData(BaseModel):
    """The data associated with an user.

    This model is used for creating and editing users.
    """

    model_config = {"from_attributes": True}

    name: str = Field(
        ...,
        title="A string unique inside parent tenant.",
        description=(
            "This needs to be a non-empty, lower case, alpa-numeric string."
        ),
    )

    @field_validator("name")
    def name_is_valid(cls, v):
        """Validate the name."""
        return user_name_is_valid(v)


def duplicate_user(user_name: str):
    """Return a 409 response for a user that already exists."""
    return JSONResponse(
        status_code=409,
        content={
            "message": (
                f"A user with a `{user_name}` user name already exists "
                "withing this tenant."
            ),
        },
    )


@my_router.get(
    "/", response_model=List[int], dependencies=[CoreSecurity("users:r")]
)
async def get_users(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
):
    """Get a list of all unique user IDs available in this application."""
    results = await context.session.scalars(
        select_user_by_slug(app_slug, tn_slug).options(load_only(User.id))
    )
    return [x.id for x in results]


async def create_user_impl(
    context: ContextDep,
    app_slug: str,
    tn_id: int,
    username: str,
    password: Optional[str] = None,
    **kwargs,
) -> Union[Tuple[User, Role, List[str]], JSONResponse]:
    """Create a new user.

    Args:
        context: The context.
        app_slug: The application slug.
        tn_id: The tenant ID.
        username: The user name.
        **kwargs: The user data.

    Returns:
        The user, the role (if any) and the permissions (if any).
        If there is already a user with the same name, a 409 response is
        returned.
    """
    # Check if the user name already exists.
    existing_count: int = cast(
        int,
        await context.session.scalar(
            select(func.count())
            .where(User.name == username)
            .join(
                User.tenant,
            )
            .filter(
                Tenant.id == tn_id,
            )
            .join(
                Tenant.application,
            )
            .filter(
                Application.slug == app_slug,
            )
        ),
    )
    if existing_count > 0:
        return duplicate_user(username)

    # Create the new user.
    assert "password" not in kwargs
    if password is not None:
        password = context.pwd_context.hash(password)

    new_rec = User(name=username, tenant_id=tn_id, password=password, **kwargs)
    context.session.add(new_rec)

    # Assign the default role, if any.
    # TODO: The default role should be a setting of the tenant.
    if context.settings.ep.default_user_role:
        query = await context.session.execute(
            select(Role)
            .join(Role.tenant)
            .filter(Tenant.id == tn_id)
            .join(Tenant.application)
            .filter(Application.slug == app_slug)
            .join(Tenant.roles)
            .filter(Role.name == context.settings.ep.default_user_role)
            .options(joinedload(Role.permissions))
        )
        try:
            role: Role = query.scalar_one()
            new_rec.roles.add(role)
            permissions = role.get_permission_names()
        except NoResultFound:
            context.logger.error(
                "The default role `%s` does not exist in the tenant `%s`.",
            )
            permissions = []
            role = None

    # Save the user and the association with the role (if any).
    await context.session.commit()
    await context.session.refresh(new_rec)

    return new_rec, role, permissions


@my_router.put(
    "/",
    responses={**e409},
    response_model=UserData,
    dependencies=[
        CoreSecurity("user:c"),
    ],
)
async def create_user(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_id: TenantIdArg,
    data: UserData = Body(),
) -> Union[UserData, JSONResponse]:
    """Create a new user."""

    # Check if the user name already exists.
    # if await context.session.scalar(
    #     select_user_by_id(app_id, tn_id, name=data.name)
    # ):
    #     return duplicate_user(data.name)

    # Create the new user.
    # new_rec = User(name=data.name, tenant_id=tn_id)
    # context.session.add(new_rec)

    # Shape the data.
    user_data = data.model_dump()
    del user_data["name"]

    # Create the new user.
    result = await create_user_impl(
        context, app_slug, tn_id, username=data.name, **user_data
    )

    # Failure?
    if isinstance(result, JSONResponse):
        return result

    # Log the event.
    new_rec = result[0]
    context.logger.info(
        f"New user {new_rec.name} created in tenant "
        f"{new_rec.tenant_id} through create user endpoint"
    )

    return UserData.model_validate(new_rec)


@my_router.get(
    "/{user_id}",
    responses={**e404},
    response_model=UserData,
    dependencies=[
        CoreSecurity("user:r"),
    ],
)
async def get_user(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    user_id: int = Path(..., title="The ID of the user to retrieve."),
):
    """Get information about a specific user."""
    query = await context.session.execute(
        select(User)
        .filter(
            User.id == user_id,
        )
        .join(
            User.tenant,
        )
        .filter(
            Tenant.slug == tn_slug,
        )
        .join(
            Tenant.application,
        )
        .filter(
            Application.slug == app_slug,
        )
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_user(user_id)
    return UserData.model_validate(result)


@my_router.post(
    "/{user_id}",
    responses={**e404, **e409},
    response_model=UserData,
    dependencies=[
        CoreSecurity("user:u"),
    ],
)
async def edit_user(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    user_id: int = Path(..., title="The ID of the user to edit."),
    data: UserData = Body(),
):
    """Edit an existing user."""
    # Locate requested record.
    query = await context.session.execute(
        select_user_by_slug(app_slug, tn_slug, id=user_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_user(user_id)

    # Check if the user-name already exists.
    if await context.session.scalar(
        select_user_by_slug(app_slug, tn_slug, name=data.name).filter(
            User.id != result.id
        )
    ):
        return duplicate_user(data.name)

    # Update the record.
    result.name = data.name
    await context.session.commit()

    return UserData.model_validate(result)


@my_router.delete(
    "/{user_id}",
    responses={**e404},
    response_model=UserData,
    dependencies=[
        CoreSecurity("user:d"),
    ],
)
async def delete_user(
    context: ContextDep,
    app_slug: AppSlugArg,
    tn_slug: TenantSlugArg,
    user_id: int = Path(..., title="The ID of the user to delete."),
):
    """Delete an existing user."""
    # Locate requested record.
    query = await context.session.execute(
        select_user_by_slug(app_slug, tn_slug, id=user_id)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_user(user_id)

    # Delete the record.
    await context.session.delete(result)
    await context.session.commit()
    return UserData.model_validate(result)


@my_router.get("/me")
async def read_users_me(current_user: AuthUserDep):
    return current_user


router.include_router(my_router)
