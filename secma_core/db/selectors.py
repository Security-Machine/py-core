from sqlalchemy.future import select
from sqlalchemy.sql.selectable import Select

from secma_core.db.models.application import Application
from secma_core.db.models.permission import Permission
from secma_core.db.models.role import Role
from secma_core.db.models.tenant import Tenant
from secma_core.db.models.user import User


def select_perm_by_slug(app_slug: str, tn_slug: str, **kwargs) -> Select:
    """Creates the select statement for permissions.

    The function uses the slug to filter by tenant and application.

    Args:
        app_slug (str): The slug of the application where this permission
            belongs to.
        tn_slug (str): The slug of the tenant where this permission belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the Permission model.

    Returns:
        The select statement.
    """
    return (
        select(Permission)
        .filter(*[getattr(Permission, k) == v for k, v in kwargs.items()])
        .join(Permission.tenant)
        .filter(Tenant.slug == tn_slug)
        .join(Tenant.application)
        .filter(Application.slug == app_slug)
    )


def select_perm_by_id(app_id: int, tn_id: int, **kwargs) -> Select:
    """Creates the select statement for permissions.

    The function uses the ID to filter by tenant and application.

    Args:
        app_id (str): The ID of the application where this permission
            belongs to.
        tn_id (str): The ID of the tenant where this permission belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the Permission model.

    Returns:
        The select statement.
    """
    return (
        select(Permission)
        .filter(*[getattr(Permission, k) == v for k, v in kwargs.items()])
        .filter(Permission.tenant_id == tn_id)
        .join(Permission.tenant)
        .filter(Tenant.application_id == app_id)
    )


def select_role_by_slug(app_slug: str, tn_slug: str, **kwargs) -> Select:
    """Creates the select statement for roles.

    The function uses the slug to filter by tenant and application.

    Args:
        app_slug (str): The slug of the application where this role
            belongs to.
        tn_slug (str): The slug of the tenant where this role belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the `Role` model.

    Returns:
        The select statement.
    """
    return (
        select(Role)
        .filter(*[getattr(Role, k) == v for k, v in kwargs.items()])
        .join(Role.tenant)
        .filter(Tenant.slug == tn_slug)
        .join(Tenant.application)
        .filter(Application.slug == app_slug)
    )


def select_role_by_id(app_id: int, tn_id: int, **kwargs) -> Select:
    """Creates the select statement for roles.

    The function uses the ID to filter by tenant and application.

    Args:
        app_id (str): The ID of the application where this role
            belongs to.
        tn_id (str): The ID of the tenant where this role belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the `Role` model.

    Returns:
        The select statement.
    """
    return (
        select(Role)
        .filter(*[getattr(Role, k) == v for k, v in kwargs.items()])
        .filter(Role.tenant_id == tn_id)
        .join(Role.tenant)
        .filter(Tenant.application_id == app_id)
    )


def select_user_by_slug(app_slug: str, tn_slug: str, **kwargs) -> Select:
    """Creates the select statement for users.

    The function uses the slug to filter by tenant and application.

    Args:
        app_slug (str): The slug of the application where this user
            belongs to.
        tn_slug (str): The slug of the tenant where this user belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the `User` model.

    Returns:
        The select statement.
    """
    return (
        select(User)
        .filter(*[getattr(User, k) == v for k, v in kwargs.items()])
        .join(User.tenant)
        .filter(Tenant.slug == tn_slug)
        .join(Tenant.application)
        .filter(Application.slug == app_slug)
    )


def select_user_by_id(app_id: int, tn_id: int, **kwargs) -> Select:
    """Creates the select statement for users.

    The function uses the ID to filter by tenant and application.

    Args:
        app_id (str): The ID of the application where this user
            belongs to.
        tn_id (str): The ID of the tenant where this user belongs to.
        **kwargs: Each key-value pair is used to construct an equality filter;
            keys must be valid column names of the `User` model.

    Returns:
        The select statement.
    """
    return (
        select(User)
        .filter(*[getattr(User, k) == v for k, v in kwargs.items()])
        .filter(User.tenant_id == tn_id)
        .join(User.tenant)
        .filter(Tenant.application_id == app_id)
    )
