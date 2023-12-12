from typing import TYPE_CHECKING, Set

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from secma_core.db.models.mixins import Common

from .base import Base, tables_prefix

if TYPE_CHECKING:
    from .permission import Permission
    from .tenant import Tenant
    from .user import User


perm2role = Table(
    f"{tables_prefix}perm2role",
    Base.metadata,
    Column("perm_id", ForeignKey(f"{tables_prefix}perms.id")),
    Column("role_id", ForeignKey(f"{tables_prefix}roles.id")),
    comment="Permission to role association.",
)

user2role = Table(
    f"{tables_prefix}user2role",
    Base.metadata,
    Column("user_id", ForeignKey(f"{tables_prefix}users.id")),
    Column("role_id", ForeignKey(f"{tables_prefix}roles.id")),
    comment="User to role association.",
)


class Role(Common, Base):
    """A role groups permissions together and can be associated with users.

    The role's name must be unique within the parent tenant.
    """

    __table_suffix__ = "roles"

    name: Mapped[str] = mapped_column(
        unique=True, index=True, comment="The name of this role."
    )
    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{tables_prefix}tenants.id",
            comment="Tenant ID where this role belongs to.",
        )
    )
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="roles",
    )
    perms: Mapped[Set["Permission"]] = relationship(
        secondary=perm2role,
        back_populates="roles",
        primaryjoin=f"Role.id == {tables_prefix}perm2role.c.role_id",
        secondaryjoin=(f"{tables_prefix}perm2role.c.perm_id == Permission.id"),
    )
    users: Mapped[Set["User"]] = relationship(
        secondary=user2role,
        back_populates="roles",
        primaryjoin=f"Role.id == {tables_prefix}user2role.c.role_id",
        secondaryjoin=(f"{tables_prefix}user2role.c.user_id == User.id"),
    )

    def __repr__(self):
        return "<Role('%s', '%s')>" % (self.id, self.name)
