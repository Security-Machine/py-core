from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, Union, cast

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.models.user import User
from secma_core.db.selectors import select_user_by_slug
from secma_core.server.app import app
from secma_core.server.constants import MANAGEMENT_APP, MANAGEMENT_TENANT
from secma_core.server.dependencies.auth import auth_error
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.settings import ManagementSettings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(
        data, settings.token_secret, algorithm=settings.token_algorithm
    )
    return encoded_jwt


@app.post("/token", response_model=Token)
async def login(
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
    ignore = SecurityScopes()
    if not form_data.username:
        raise auth_error(context.logger, ignore, "No username in form")

    # Locate requested user.
    user_query = await context.session.execute(
        select_user_by_slug(
            MANAGEMENT_APP, MANAGEMENT_TENANT, name=form_data.username
        ).options(
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
    if not pwd_context.verify(form_data.password, user.password):
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
