"""Entry point for the WSGI application.

Run this script without arguments to start the server.
"""

import logging
from contextlib import asynccontextmanager
from typing import Awaitable, Callable, Optional, cast
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.utils import is_body_allowed_for_status_code
from log4me import setup_logging
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from secma_core.db.main import connect_to_database
from secma_core.server.app import create_app
from secma_core.server.constants import (
    MANAGEMENT_APP,
    MANAGEMENT_PERMS,
    MANAGEMENT_TENANT,
)
from secma_core.server.exceptions import HtmlError
from secma_core.server.settings import Settings


@asynccontextmanager
async def lifespan(local_app: FastAPI):
    """Initialize the app and dispose of it when it's done.

    This function is called by the fast-api constructor to initialize the app.

    Inside we create the database connection and session factory, and we
    initialize the database with minimum required data.

    Once the app is initialized we yield control to the caller, and once the
    caller is done we dispose of the database connection.
    """
    global engine
    global async_session
    global app
    app = local_app

    # Get the engine (database connection) and session factory.
    engine = cast(AsyncEngine, await connect_to_database(settings.database))
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Save data in the app state so it's accessible everywhere else.
    local_app.extra["engine"] = engine
    local_app.extra["async_session"] = async_session
    local_app.extra["settings"] = settings

    # Ensure that the database has minimum required data to operate.
    from secma_core.db.init_db import init_db
    from secma_core.server.management.auth import pwd_context

    try:
        m_stg = settings.management
        async with cast(async_sessionmaker, async_session)() as session:
            await init_db(
                session=session,
                app=MANAGEMENT_APP,
                tenant=MANAGEMENT_TENANT,
                perms=MANAGEMENT_PERMS,
                user=m_stg.super_user,
                password=pwd_context.hash(m_stg.super_password),
                role=m_stg.super_role,
            )
    except Exception:
        logging.getLogger("secma_core").exception(
            "Failed to initialize the database."
        )
        raise
    # Run the app.
    yield

    # Close the database connection when it's done.
    await engine.dispose()
    engine = None
    app = None


settings = Settings()
setup_logging(settings.log)
app: Optional[FastAPI] = create_app(set_global=True, lifespan=lifespan)
engine: Optional[AsyncEngine] = None
async_session: Optional[async_sessionmaker] = None
app = cast(FastAPI, app)


# Cors settings.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.net.cors_origins,
    allow_credentials=settings.net.cors_allow_credentials,
    allow_methods=settings.net.cors_allow_methods,
    allow_headers=settings.net.cors_allow_headers,
)


@app.exception_handler(HtmlError)
async def html_exception_handler(request: Request, exc: HtmlError):
    """Handle HTML errors."""
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=exc.headers)
    return exc.to_response()

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Handle exceptions."""
    unique_id = str(uuid4())
    request.state.logger.exception(exc)
    request.state.logger.error(
        "Internal server error (trace id: %s)", unique_id
    )
    return JSONResponse(
        content={
            "message": (
                "Unhandled exception in server code. Please "
                "contact the administrator."
            ),
            "trace_id": unique_id,
        },
        status_code=500,
    )


@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    """Add the database session to the request."""
    request.state.settings = settings
    request.state.logger = logging.getLogger("secma_core")
    async with cast(async_sessionmaker, async_session)() as session:
        request.state.session = session
        return await call_next(request)


import secma_core.server.api  # noqa: F401 E402


def start_server():
    """Start the server.

    Use this if you want to debug the code. To simply run the server locally
    you can also use the `make run` command, which has the added benefit of
    reloading when the code changes.
    """
    import uvicorn

    print("Starting security machine core...")
    uvicorn.run(app, host="localhost", port=8989)


if __name__ == "__main__":
    start_server()
