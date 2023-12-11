"""Collects all routes for the application.

If you plan to create a custom application with only some of the routes
then create your own ``api.py`` file and import the routes you need from
the ``secma_core.server`` module, then create a ``main.py`` file that
uses this api modeled on the ``main.py`` file in this directory.
"""
from typing import cast

from .app import FastAPI, app
from .management.api import router as management_router
from .permissions.api import router as perm_router
from .tenants.api import router as tenants_router
from .users.api import router as users_router

app = cast(FastAPI, app)
app.include_router(management_router)
app.include_router(tenants_router)
app.include_router(users_router)
app.include_router(perm_router)
