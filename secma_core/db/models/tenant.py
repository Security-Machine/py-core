from typing import TYPE_CHECKING, Optional, Set

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from secma_core.db.models.mixins import Common

from .base import Base, tables_prefix

if TYPE_CHECKING:
    from .application import Application
    from .permission import Permission
    from .role import Role
    from .user import User


class Tenant(Common, Base):
    """The tenant in an application.

    The tenant is the second level of partitioning in the data stored by the
    core library. The first level is the application.

    The tenant includes the users that can access the data, the permissions
    that can be assigned to the users, roles (groups of permissions), the
    list of users and the connection between users and roles.
    """

    __table_suffix__ = "tenants"
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="A title for the application.", default=None,
    )
    slug: Mapped[str] = mapped_column(
        index=True, comment="Tenant unique slug used in URLs."
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{tables_prefix}applications.id",
            comment="Application ID that this tenant belongs to.",
        )
    )
    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="tenants",
    )
    users: Mapped[Set["User"]] = relationship(
        "User",
        back_populates="tenant",
    )
    roles: Mapped[Set["Role"]] = relationship(
        "Role",
        back_populates="tenant",
    )
    perms: Mapped[Set["Permission"]] = relationship(
        "Permission",
        back_populates="tenant",
    )

    def __repr__(self):
        return "<Tenant('%s', '%s')>" % (self.id, self.slug)
