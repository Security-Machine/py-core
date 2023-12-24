from logging import Logger
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, Request, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.role import Role
from secma_core.db.models.user import User
from secma_core.db.selectors import select_user_by_slug
from secma_core.server.constants import (
    MANAGEMENT_APP,
    MANAGEMENT_PERMS,
    MANAGEMENT_TENANT,
)
from secma_core.server.exceptions import HttpError
from secma_core.server.messages import get_err
from secma_core.server.settings import ManagementSettings

from .user import UserContext

# OAuth2 scheme for authentication. We use it to retrieve the token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=MANAGEMENT_PERMS,
)

# Use with a dependency argument to get the current token.
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def auth_error(
    logger: Logger,
    permissions: SecurityScopes,
    message: str,
    is_auth: bool = True,
    exc_info: bool = False,
):
    """Return an authentication error.

    Args:
        logger: The logger to be used.
        permissions: The permissions required for the endpoint.
        message: The message to be logged.
        is_auth: Whether the error is an authentication error or an
            authorization error.

    Returns:
        The HTTP exception.
    """
    if permissions.scopes:
        authenticate_value = f'Bearer scope="{permissions.scope_str}"'
    else:
        authenticate_value = "Bearer"

    # We generate a unique ID for the error so that we can tie opaque info
    # sent to the user with the error in the logs.
    unique_id = str(uuid4())

    if is_auth:
        detail = get_err("invalid-credentials", params={"uniqueId": unique_id})
    else:
        detail = get_err("no-permission", params={"uniqueId": unique_id})

    # Log the error.
    logger.error("%s - %s", message, detail.message, exc_info=exc_info)

    # Return the error to be raised by the caller.
    return HttpError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        data=detail,
        headers={"WWW-Authenticate": authenticate_value},
    )


async def get_current_user(
    request: Request, permissions: SecurityScopes, token: TokenDep
) -> UserContext:
    """Retrieve the user for current request.

    The user must belong to the management application and be part
    of the management tenant.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        request: The request.
        permissions: All permissions required for the endpoint that is
            being accessed.
        token: The token provided in the request.

    Returns:
        The user associated with the token.
    """
    # Get prepared data.
    session: AsyncSession = request.state.session
    settings: ManagementSettings = request.state.settings.management
    logger: Logger = request.state.logger
    req_perm = set(permissions.scopes)

    # Extract data from token.
    try:
        payload = jwt.decode(
            token,
            settings.token_secret.get_secret_value(),
            algorithms=[settings.token_algorithm],
        )
    except JWTError:
        raise auth_error(
            logger, permissions, "Invalid token in request", exc_info=True
        )
    username: str = payload.get("sub")
    token_scopes = set(payload.get("scopes", []))

    # Check that there is data in the token.
    if not username:
        raise auth_error(logger, permissions, "No username in token")
    if len(token_scopes) == 0:
        raise auth_error(
            logger, permissions, "No permissions in token", is_auth=False
        )

    # Locate requested user.
    user_query = await session.execute(
        select_user_by_slug(
            MANAGEMENT_APP, MANAGEMENT_TENANT, name=username
        ).options(
            joinedload(User.roles),
            joinedload(User.roles).joinedload(Role.perms),
        )
    )
    try:
        user = user_query.unique().scalar_one()
    except NoResultFound:
        raise auth_error(logger, permissions, "No `{username}` user found")
    user_perms = user.get_permissions()

    # Make sure it is not suspended.
    if user.suspended:
        raise auth_error(
            logger, permissions, f"User `{username}` is suspended"
        )

    # Go through all permissions and check that the token has them.
    if not req_perm.issubset(token_scopes):
        raise auth_error(
            logger,
            permissions,
            f"Missing permissions in token: {req_perm-token_scopes}",
            is_auth=False,
        )

    # Go through all permissions and check that the user has them.
    if not req_perm.issubset(user_perms):
        raise auth_error(
            logger,
            permissions,
            f"Missing permissions in database: {req_perm-user_perms}",
            is_auth=False,
        )

    # Log success.
    logger.info("User %s authenticated, authorized for %s", user, req_perm)

    # Construct result.
    return UserContext(
        request=request,
        session=session,
        app_slug=MANAGEMENT_APP,
        tn_slug=MANAGEMENT_TENANT,
        user=user,
        logger=logger,
    )


AuthUserDep = Annotated[User, Depends(get_current_user)]


def CoreSecurity(*args: str) -> Any:
    """Dependency that checks the permissions of the user.

    Args:
        args: The permissions that the user needs to be allowed
            to access this path.

    Returns:
        The dependency to add to your function.
    """
    scopes = []
    for s in args:
        if s not in MANAGEMENT_PERMS:
            raise ValueError(
                f"Unknown permission: {s}. Add it to `MANAGEMENT_PERMS`."
            )
        scopes.append(s)
    return Security(get_current_user, scopes=scopes)
