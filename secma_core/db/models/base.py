import os

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr

tables_prefix = os.environ.get("SECURITY_MACHINE_TABLE_PREFIX", "secma_")
schema = os.environ.get("SECURITY_MACHINE_DB_SCHEMA", "")
_args = {"schema": schema} if len(schema) else {}


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""

    @declared_attr.directive
    def __tablename__(cls):
        return tables_prefix + cls.__table_suffix__

    __table_args__ = _args
