from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.future import select

from secma_core.db.models.application import Application
from secma_core.db.models.permission import Permission
from secma_core.db.models.role import Role
from secma_core.db.models.tenant import Tenant
from secma_core.db.models.user import User
from secma_core.server.dependencies.auth import CoreSecurity
from secma_core.server.dependencies.context import ContextDep

from . import router


class StatisticsReply(BaseModel):
    """General statistics about the database."""

    apps: int = Field(
        ..., description="The number of applications in the database."
    )
    apps_no_tenants: int = Field(
        ..., description="The number of applications without any tenant."
    )
    tenants: int = Field(
        ..., description="The number of tenants in the database."
    )
    tenants_no_users: int = Field(
        ..., description="The number of tenants without any user."
    )
    tenants_no_roles: int = Field(
        ..., description="The number of tenants without any role."
    )
    tenants_no_perms: int = Field(
        ..., description="The number of tenants without any permission."
    )
    users: int = Field(..., description="The number of users in the database.")
    users_no_roles: int = Field(
        ..., description="The number of users without any role."
    )
    roles: int = Field(..., description="The number of roles in the database.")
    roles_no_perms: int = Field(
        ..., description="The number of roles without any permission."
    )
    perms: int = Field(
        ..., description="The number of permissions in the database."
    )


@router.get("/stats", response_model=StatisticsReply, dependencies=[
    CoreSecurity("stats:r")
])
async def api_version(context: ContextDep) -> StatisticsReply:
    """Return the API version."""
    # Query the database.
    stmt = select(
        select(func.count(Application.id)).subquery(),
        select(func.count(Tenant.id)).subquery(),
        select(func.count(User.id)).subquery(),
        select(func.count(Role.id)).subquery(),
        select(func.count(Permission.id)).subquery(),
        select(
            func.count(Application.id).filter(
                Application.tenants == None  # noqa: E711
            )
        ).subquery(),
        select(
            func.count(Tenant.id).filter(Tenant.users == None)  # noqa: E711
        ).subquery(),
        select(
            func.count(Tenant.id).filter(Tenant.roles == None)  # noqa: E711
        ).subquery(),
        select(
            func.count(Tenant.id).filter(Tenant.perms == None)  # noqa: E711
        ).subquery(),
        select(
            func.count(User.id).filter(User.roles == None)  # noqa: E711
        ).subquery(),
        select(
            func.count(Role.id).filter(Role.perms == None)  # noqa: E711
        ).subquery(),
    )
    # Execute the query
    results = await context.session.execute(stmt)
    # Unpack the counts
    (
        apps_count,
        tenants_count,
        users_count,
        roles_count,
        perms_count,
        apps_no_tenants,
        tenants_no_users,
        tenants_no_roles,
        tenants_no_perms,
        users_no_roles,
        roles_no_perms,
    ) = list(results)[0]

    return StatisticsReply(
        apps=apps_count,
        tenants=tenants_count,
        users=users_count,
        roles=roles_count,
        perms=perms_count,
        apps_no_tenants=apps_no_tenants,
        tenants_no_users=tenants_no_users,
        tenants_no_roles=tenants_no_roles,
        tenants_no_perms=tenants_no_perms,
        users_no_roles=users_no_roles,
        roles_no_perms=roles_no_perms,
    )
