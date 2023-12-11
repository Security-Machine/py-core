from datetime import datetime
from typing import TYPE_CHECKING, Optional, Set

from sqlalchemy import DateTime, FetchedValue, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Common:
    id: Mapped[int] = mapped_column(
        primary_key=True, comment="Unique ID of this record"
    )
    description: Mapped[Optional[str]] = mapped_column(
        comment="A description for this record.", default=None
    )
    created: Mapped[datetime] = mapped_column(
        comment="The moment when this record was created.",
        default=func.now(),
        server_default=FetchedValue()
    )
    updated: Mapped[datetime] = mapped_column(
        comment="The last time when this record was updated.",
        onupdate=func.now(),
        default=func.now(),
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
    )
