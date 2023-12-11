from typing import Dict, Tuple

from attrs import define
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from secma_core.db.models.application import Application
from secma_core.db.models.permission import Permission
from secma_core.db.models.role import Role
from secma_core.db.models.tenant import Tenant
from secma_core.db.models.user import User


@define
class InitDbResult:
    """The result of initializing the database."""

    app: Application
    is_app_new: bool
    tenant: Tenant
    is_t_new: bool
    user: User
    is_u_new: bool
    role: Role
    is_r_new: bool
    perms: Dict[str, Tuple[Permission, bool]]
    has_new_perms: bool


async def init_db(
    session: AsyncSession,
    app: str,
    tenant: str,
    perms: Dict[str, str],
    user: str,
    password: str,
    role: str,
):
    """Initialize the database with minimum required data.

    Args:
        session: The database session.
        app: The name of the app management application.
        tenant: The name of the tenant inside management app.
        perms: The permissions create and associate with `role`.
        user: The name of the super-user which has all permissions.
        password: The password of the super-user.
        role: The name of the role that includes all permissions.
    """
    import secma_core.db.models.api  # noqa: F401
    with session.no_autoflush:
        # Ensure that the app exists.
        db_app, is_app_new = await session.scalar(
            select(Application).filter(Application.slug == app)
        ), False
        if db_app is None:
            db_app = Application(slug=app)
            session.add(db_app)
            is_app_new = True

        # Ensure that the tenant exists.
        db_tenant = None
        if not is_app_new:
            db_tenant, is_t_new = await session.scalar(
                select(Tenant).filter(
                    Tenant.slug == tenant,
                    Tenant.application_id == db_app.id,
                )
            ), False
        if db_tenant is None:
            db_tenant = Tenant(slug=tenant, application=db_app)
            session.add(db_tenant)
            is_t_new = True

        # Ensure that the super-user exists.
        db_user = None
        if not is_t_new:
            db_user, is_u_new = await session.scalar(
                select(User).filter(
                    User.name == user,
                    User.tenant_id == db_tenant.id,
                ).options(
                    joinedload(User.roles),
                )
            ), False
        if db_user is None:
            db_user = User(name=user, tenant=db_tenant, password=password)
            session.add(db_user)
            is_u_new = True

        # Ensure that the super-role exists.
        db_role = None
        if not is_t_new:
            db_role, is_r_new = await session.scalar(
                select(Role).filter(
                    Role.name == role,
                    Role.tenant_id == db_tenant.id,
                ).options(
                    joinedload(Role.perms),
                )
            ), False
        if db_role is None:
            db_role = Role(name=role, tenant=db_tenant)
            session.add(db_role)
            is_r_new = True

        # Go through each permission and ensure it exists.
        db_perms, has_new_perms = {}, False
        for perm, description in perms.items():
            db_perm = None
            if not is_t_new:
                db_perm, is_p_new = await session.scalar(
                    select(Permission).filter(
                        Permission.name == perm,
                        Permission.tenant_id == db_tenant.id,
                    )
                ), False
            if db_perm is None:
                db_perm = Permission(
                    name=perm, description=description, tenant=db_tenant
                )
                session.add(db_perm)
                is_p_new = True
                has_new_perms = True
            db_perms[perm] = (db_perm, is_p_new)

        # The user must have the role.
        (await db_user.awaitable_attrs.roles).add(db_role)

        # The role must have all permissions.
        for db_perm, _ in db_perms.values():
            (await db_role.awaitable_attrs.perms).add(db_perm)

    # Save these changes.
    await session.commit()

    return InitDbResult(
        app=db_app,
        is_app_new=is_app_new,
        tenant=db_tenant,
        is_t_new=is_t_new,
        user=db_user,
        is_u_new=is_u_new,
        role=db_role,
        is_r_new=is_r_new,
        perms=db_perms,
        has_new_perms=has_new_perms,
    )
