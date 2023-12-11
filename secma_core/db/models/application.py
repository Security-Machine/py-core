from typing import TYPE_CHECKING, Optional, Set
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from secma_core.db.models.mixins import Common

from .base import Base

if TYPE_CHECKING:
    from .tenant import Tenant


class Application(Common, Base):
    """The Application model.

    This is the top level that partitions the data stored by the core library.
    To be able to use the library, an application must be created first.

    The application will include one or more tenants, which include the users
    that can access the data, the permissions that can be assigned to the users
    and their relations.
    """

    __table_suffix__ = "applications"
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="A title for the application.", default=None,
    )
    slug: Mapped[str] = mapped_column(
        unique=True, index=True, comment="Application unique slug used in URL."
    )
    tenants: Mapped[Set["Tenant"]] = relationship(
        "Tenant",
        back_populates="application",
    )

    def __repr__(self):
        return "<App('%s', '%s')>" % (self.id, self.slug)
