from typing import TYPE_CHECKING, Set

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from secma_core.db.models.mixins import Common

from .base import Base, tables_prefix

if TYPE_CHECKING:
    from .role import Role
    from .tenant import Tenant


class Permission(Common, Base):
    """A permission identifies a resource and the action that can be performed.

    The permission's name must be unique within the parent tenant.

    For a given resource, say a `Post`, there can be multiple permissions:

    - `post:read`
    - `post:write`
    - `post:delete`
    - `post:create`

    The library assigns no special meaning to the permission name, it is up to
    the application using it to decide what permissions are needed
    and what they mean.
    """

    __table_suffix__ = "perms"

    name: Mapped[str] = mapped_column(
        unique=True, index=True, comment="The name of this permission."
    )
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{tables_prefix}tenants.id",
            comment="Tenant ID where this permission belongs to.",
        )
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="perms",
    )
    roles: Mapped[Set["Role"]] = relationship(
        "Role",
        back_populates="perms",
        secondary=f"{tables_prefix}perm2role",
        primaryjoin=(
            f"{tables_prefix}perm2role.c.perm_id == Permission.id"
        ),
        secondaryjoin=(
            f"{tables_prefix}perm2role.c.role_id == Role.id"
        ),
    )

    def __repr__(self):
        return "<Perm('%s', '%s')>" % (self.id, self.name)
