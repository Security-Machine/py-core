from typing import TYPE_CHECKING, Optional, Set

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from secma_core.db.models.mixins import Common

from .base import Base, tables_prefix

if TYPE_CHECKING:
    from .role import Role
    from .tenant import Tenant


class User(Common, Base):
    """A user that belongs to a tenant in an application.

    Users have unique names within their tenants. A user can be associated
    with zero or more roles, which in turn are associated with zero or more
    permissions.
    """

    __table_suffix__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True, comment="Unique ID for this user"
    )
    name: Mapped[str] = mapped_column(
        index=True, comment="The name of this user."
    )
    password: Mapped[Optional[str]] = mapped_column(
        comment="The password of this user.", default=None
    )
    suspended: Mapped[bool] = mapped_column(
        default=False,
        comment="Whether this user is suspended and cannot log in.",
    )
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{tables_prefix}tenants.id",
            comment="Tenant ID where this user belongs to.",
        )
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
    )
    roles: Mapped[Set["Role"]] = relationship(
        "Role",
        back_populates="users",
        secondary=f"{tables_prefix}user2role",
        primaryjoin=(
            f"{tables_prefix}user2role.c.user_id == {tables_prefix}users.c.id"
        ),
        secondaryjoin=(
            f"{tables_prefix}user2role.c.role_id == {tables_prefix}roles.c.id"
        ),
    )

    def __repr__(self):
        return "<User('%s', '%s')>" % (self.id, self.name)

    def get_permissions(self) -> Set[str]:
        """Get the permissions associated with this user.

        Returns:
            The permission names associated with this user.
        """
        permissions = set()
        for role in self.roles:
            for perm in role.perms:
                permissions.add(perm.name)
        return permissions
