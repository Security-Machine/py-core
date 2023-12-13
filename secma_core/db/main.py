from __future__ import annotations

import os
from asyncio import sleep
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from db4me import AllDatabaseSettings, get_engine
from sqlalchemy import Engine, MetaData

from secma_core.db.models.api import Base

# The path to this folder.
this_folder = os.path.dirname(os.path.realpath(__file__))

# The path to the alembic config file.
alembic_config = os.path.join(this_folder, "alembic.ini")


@contextmanager
def get_alembic_config(engine: Engine):
    """Get the alembic config.

    Args:
        engine: The connection to the database.
    Yields:
        The alembic config.
    """
    with engine.begin() as connection:
        alembic_cfg = Config(alembic_config)
        alembic_cfg.attributes["connection"] = connection
        current_dir = os.getcwd()
        os.chdir(this_folder)
        yield alembic_cfg
        os.chdir(current_dir)


def create_tables(engine: Engine):
    """Create all tables in the database.

    Args:
        engine: The database engine.
    """
    # Create all tables.
    with engine.begin() as conn:
        Base.metadata.create_all(conn)

    # Load the Alembic configuration and generate the
    # version table, "stamping" it with the most recent rev:
    with get_alembic_config(engine) as alembic_cfg:
        command.stamp(alembic_cfg, "head")


def run_migrations(engine: Engine):
    """Run migrations on the database.

    Args:
        engine: The database engine.
    """
    with get_alembic_config(engine) as alembic_cfg:
        command.upgrade(alembic_cfg, "head")


def sync_tables(sync_engine: Engine):
    metadata_obj = MetaData()
    metadata_obj.reflect(bind=sync_engine)
    return [table.name for table in metadata_obj.sorted_tables]


async def connect_to_database(settings: AllDatabaseSettings):
    """Connect to the database.

    Args:
        connection_string: The connection string to the database
    Returns:
        The connection to the database.
    """
    # I was unable to make alembic use the async engine.
    # So, if we are using an async engine, we need to use
    # a sync alternative for this part.
    if not settings.db.sync_alternative:
        raise ValueError(
            "A sync_alternative is required in database settings "
            "for async connections"
        )
    sync_engine: Engine = get_engine(settings, is_async=False)
    sync_table_names = sync_tables(sync_engine)

    if not sync_table_names:
        create_tables(sync_engine)
    else:
        run_migrations(sync_engine)
    await sleep(0.5)

    engine = get_engine(settings, is_async=True)

    # Make sure the async engine is working.
    async with engine.begin() as conn:
        table_names = await conn.run_sync(engine.dialect.get_table_names)
    sync_table_names = sync_tables(sync_engine)
    assert len(table_names) == len(sync_table_names)

    return engine
