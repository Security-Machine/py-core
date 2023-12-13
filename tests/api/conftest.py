import logging
from pathlib import Path
import os.path
import sys
from typing import List, TYPE_CHECKING, cast
from uuid import uuid4
import pytest
import shutil
from fastapi.testclient import TestClient as TestClientBase
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker


if TYPE_CHECKING:
    from secma_core.server.settings import Settings


class TestClient(TestClientBase):
    @property
    def app_settings(self) -> "Settings":
        return self.app.extra["settings"]

    @property
    def db_engine(self) -> AsyncEngine:
        return self.app.extra["engine"]

    @property
    def token_secret(self) -> str:
        return self.app_settings.management.token_secret.get_secret_value()

    @property
    def super_password(self) -> str:
        return self.app_settings.management.super_password.get_secret_value()

    @property
    def super_user(self) -> str:
        return self.app_settings.management.super_user


@pytest.fixture
def client(tmp_path: Path, monkeypatch, request):
    """A pytest fixture to get a test client for the FastAPI app.

    Args:
        tmp_path: The temporary path provided by pytest.

    Returns:
        A test client for the FastAPI app.
    """
    test_name = request.function.__name__

    # Make sure that modules are note loaded.
    to_del = [m for m in sys.modules if m.startswith("secma_core")]
    for m in to_del:
        del sys.modules[m]
        del m

    # Use a unique database for every test.
    db_name = uuid4().hex
    monkeypatch.setenv(
        "SECURITY_MACHINE_DATABASE__DB__URL",
        f"sqlite+aiosqlite:///file:{db_name}?"
        + "mode=memory&"
        + "cache=shared&"
        + "uri=true",
    )
    monkeypatch.setenv(
        "SECURITY_MACHINE_DATABASE__DB__SYNC_ALTERNATIVE",
        f"sqlite:///file:{db_name}?mode=memory&cache=shared&uri=true",
    )

    # Adjust logging.
    if os.path.isdir("./playground/logs"):
        log_dir = "./playground/logs"
    else:
        log_dir = tmp_path
    monkeypatch.setenv(
        "SECURITY_MACHINE_LOG__FILE_PATH",
        os.path.join(log_dir, test_name + "-%date%-%time%.log"),
    )
    monkeypatch.setenv("SECURITY_MACHINE_LOG__FILE_LEVEL", "10")
    monkeypatch.setenv("SECURITY_MACHINE_LOG__CONSOLE_LEVEL", "0")
    monkeypatch.setenv("SECURITY_MACHINE_LOG__CONSOLE_LEVEL", "0")

    # Remove the environment variables that may be set by other tests.
    monkeypatch.setenv(
        "SECURITY_MACHINE_MANAGEMENT__TOKEN_SECRET", "token-secret"
    )
    monkeypatch.setenv(
        "SECURITY_MACHINE_MANAGEMENT__SUPER_PASSWORD", "super-pass"
    )

    # Create a temporary configuration file.
    cfg_file = os.path.join(tmp_path, "cfg.yaml")
    src_cfg_file = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "secma_core",
        "server",
        "default-config.yaml",
    )
    shutil.copyfile(src_cfg_file, cfg_file)
    monkeypatch.setenv("SECURITY_MACHINE_CONFIG", cfg_file)

    # Replace default file handler.
    log_messages = []

    class FileHandler(logging.FileHandler):
        """A logging handler that stores messages and makes them available to
        the test.
        """

        def emit(self, record):
            log_messages.append(record)
            super().emit(record)

    # Add extra information to the log messages.
    # old_factory = logging.getLogRecordFactory()
    #
    # def record_factory(*args, **kwargs):
    #     record = old_factory(*args, **kwargs) # get the unmodified record
    #     record.test = test_name # add custom attribute
    #     record.msg = test_name + " > " + record.msg
    #     return record
    #
    # logging.setLogRecordFactory(record_factory)

    # Patch the logger.
    monkeypatch.setattr("logging.FileHandler", FileHandler)

    from secma_core.server.main import app

    with TestClient(app) as client:
        logging.getLogger("secma_core").info("Test %s started.", test_name)
        app.extra["log_messages"] = log_messages
        yield client
        logging.getLogger("secma_core").info("Test %s ended.", test_name)
        logging.shutdown()


@pytest.fixture
def token_factory(client: TestClient):
    """A pytest fixture to get a valid token."""

    def create_token(
        user_name: str = "test-user", permissions: List[str] = None
    ) -> str:
        from secma_core.server.management.auth import create_access_token
        from secma_core.server.constants import MANAGEMENT_PERMS

        permissions = permissions if permissions else []
        for s in permissions:
            if s not in MANAGEMENT_PERMS:
                raise ValueError(
                    f"Unknown permission: {s}. Add it to `MANAGEMENT_PERMS`."
                )

        return create_access_token(
            data={"sub": user_name, "scopes": permissions},
            settings=client.app_settings.management,
        )

    return create_token


@pytest.fixture
async def new_app_factory(client: TestClient):
    """A pytest fixture you can use to create a new application."""
    async_session = client.app.extra["async_session"]
    from tests.factories import Application

    async def new_app(slug: str):
        async with cast(async_sessionmaker, async_session)() as session:
            new_app = Application(slug=slug)
            session.add(new_app)
            await session.commit()
            await session.refresh(new_app)
            return new_app

    return new_app
