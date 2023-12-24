from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, Union, cast

from fastapi import Depends, FastAPI, Path
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.models.user import User
from secma_core.db.selectors import select_user_by_slug
from secma_core.server.app import app
from secma_core.server.constants import MANAGEMENT_APP, MANAGEMENT_TENANT
from secma_core.server.dependencies.auth import auth_error
from secma_core.server.dependencies.context import Context, ContextDep
from secma_core.server.dependencies.tenant import TenantIdArg
from secma_core.server.settings import ManagementSettings
from secma_core.server.users.user import create_user_impl

app = cast(FastAPI, app)


class Token(BaseModel):
    """The token response model.

    Attributes:
        access_token (str): The access token.
        token_type (str): The token type.
    """

    access_token: str
    token_type: str


def create_access_token(
    data: Dict[str, Any],
    settings: ManagementSettings,
    expires_delta: Union[timedelta, None] = None,
):
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.token_expiration
        )
    data["exp"] = expire
    encoded_jwt = jwt.encode(
        data,
        settings.token_secret.get_secret_value(),
        algorithm=settings.token_algorithm,
    )
    return encoded_jwt


async def common_login(
    context: Context, form_data: Any, app_slug: str, tenant: str
):
    """Common login function.

    Args:
        context: The context.
        form_data: The user-provided data.
        app_slug: The application slug.
        tenant: The tenant slug.
    Returns:
        The token.
    """
    ignore = SecurityScopes()

    if not context.settings.ep.allow_login:
        raise auth_error(
            context.logger,
            ignore,
            "Login using email and password is not allowed in settings",
        )

    if not form_data.username:
        raise auth_error(context.logger, ignore, "No username in form")

    # Locate requested user.
    user_query = await context.session.execute(
        select_user_by_slug(app_slug, tenant, name=form_data.username).options(
            joinedload(User.roles),
            joinedload(User.roles).joinedload(Role.perms),
        )
    )
    try:
        user: User = user_query.unique().scalar_one()
    except NoResultFound:
        raise auth_error(context.logger, ignore, "No `{username}` user found")
    user_perms = user.get_permissions()

    # Make sure it is not suspended.
    if user.suspended:
        raise auth_error(
            context.logger,
            ignore,
            f"Suspended user `{form_data.username}` attempted to login",
        )

    # Check the password.
    if not context.pwd_context.verify(form_data.password, user.password):
        raise auth_error(context.logger, ignore, "Incorrect password")

    # The required permissions must be a subset of the user permissions.
    req_perm = set(form_data.scopes)
    if len(req_perm) == 0:
        req_perm = user_perms
    else:
        # Go through all permissions and check that the user has them.
        if not req_perm.issubset(user_perms):
            raise auth_error(
                context.logger,
                ignore,
                f"Missing permissions in database: {req_perm-user_perms}",
            )

    # Create the token.
    token = create_access_token(
        data={"sub": user.name, "scopes": list(req_perm)},
        settings=context.settings.management,
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/token/{app_slug}/{tenant}", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    context: ContextDep,
    app_slug: str = Path(
        ..., title="The name of the application where the tenant belongs."
    ),
    tenant: str = Path(
        ...,
        title="The name of the tenant where the user belongs.",
    ),
):
    """Get a token that can be later used to authenticate requests.

    Args:
        form_data: The user-provided data.
        context: The context.

    Returns:
        The token.
    """
    return await common_login(context, form_data, app_slug, tenant)


@app.put("/token/{app_slug}/{tenant}", response_model=Token)
async def signup(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    context: ContextDep,
    tn_id: TenantIdArg,
    app_slug: str = Path(
        ..., title="The name of the application where the tenant belongs."
    ),
    responses=(
        {
            "status_code": 409,
            "description": "The user already exists.",
        },
    ),
):
    """Create the user and get a token that can be later used.

    Args:
        form_data: The user-provided data.
        context: The context.

    Returns:
        The token.
    """
    ignore = SecurityScopes()

    if not context.settings.ep.allow_signup:
        raise auth_error(
            context.logger,
            ignore,
            "Sign-up using email and password is not allowed in settings",
        )

    # Create the new user.
    result = await create_user_impl(
        context,
        app_slug,
        tn_id,
        username=form_data.username,
        password=form_data.password,
    )

    # Failure?
    if isinstance(result, JSONResponse):
        return result

    # Log the event.
    new_rec, _, permissions = result
    context.logger.info(
        f"New user {new_rec.name} created in tenant "
        f"{new_rec.tenant_id} through signup"
    )

    # Create the token.
    token = create_access_token(
        data={"sub": new_rec.name, "scopes": permissions},
        settings=context.settings.management,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.post("/token", response_model=Token)
async def management_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    context: ContextDep,
):
    """Get a token that can be later used to authenticate requests.

    Args:
        form_data: The user-provided data.
        context: The context.

    Returns:
        The token.
    """
    return await common_login(
        context, form_data, MANAGEMENT_APP, MANAGEMENT_TENANT
    )
