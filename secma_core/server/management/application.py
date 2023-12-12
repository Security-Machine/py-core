from typing import List, Union, cast

from fastapi import APIRouter, Body, Path
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.application import Application
from secma_core.schemas.application import ApplicationData, ApplicationInput
from secma_core.server.dependencies.auth import CoreSecurity
from secma_core.server.dependencies.context import ContextDep
from secma_core.server.utils import duplicate_app, no_app

from ..constants import e404, e409
from . import router

my_router = APIRouter(
    prefix="/apps",
)


@my_router.get(
    "/", response_model=List[str], dependencies=[CoreSecurity("apps:r")]
)
async def get_apps(context: ContextDep):
    """Get a list of all unique application slugs available to this core."""

    results = await context.session.scalars(
        select(Application).options(load_only(Application.slug))
    )
    return [x.slug for x in results]


@my_router.put(
    "/",
    responses={**e409},
    response_model=ApplicationData,
    dependencies=[
        CoreSecurity("app:c"),
    ],
)
async def create_app(
    context: ContextDep,
    data: ApplicationInput = Body(),
) -> Union[ApplicationData, JSONResponse]:
    """Create a new application."""
    session: AsyncSession = context.session
    with session.no_autoflush:
        # Check if the slug already exists.
        result: int = cast(
            int,
            await session.scalar(
                select(func.count()).where(Application.slug == data.slug)
            ),
        )
        if result > 0:
            return duplicate_app(data.slug)

        # Create the new application.
        new_app = Application(
            slug=data.slug,
            title=data.title,
            description=data.description,
        )
        session.add(new_app)
        await session.commit()

        await session.refresh(new_app)
        return ApplicationData.model_validate(new_app)

        # return ApplicationData.model_validate(
        #     slug=new_app.slug,
        #     title=new_app.title,
        #     description=new_app.description,
        #     created=await new_app.created,
        #     updated=await new_app.updated,
        # )


@my_router.get(
    "/{app_slug}",
    responses={**e404},
    response_model=ApplicationData,
    dependencies=[
        CoreSecurity("app:r"),
    ],
)
async def get_app(
    context: ContextDep,
    app_slug: str = Path(..., title="The name of the application to get."),
):
    """Get information about a specific application."""
    query = await context.session.execute(
        select(Application).where(Application.slug == app_slug)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_app(app_slug)
    return ApplicationData.model_validate(result)


@my_router.post(
    "/{app_slug}",
    responses={**e404, **e409},
    response_model=ApplicationData,
    dependencies=[
        CoreSecurity("app:u"),
    ],
)
async def edit_app(
    context: ContextDep,
    app_slug: str,
    data: ApplicationInput = Body(),
):
    """Edit an existing application."""
    # Locate requested record.
    query = await context.session.execute(
        select(Application).where(Application.slug == app_slug)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_app(app_slug)

    # Check if the slug already exists.
    if await context.session.scalar(
        select(Application).filter(
            Application.slug == data.slug,
            Application.id != result.id,
        )
    ):
        return duplicate_app(data.slug)

    # Update the record.
    result.slug = data.slug
    result.title = data.title
    result.description = data.description
    await context.session.commit()
    await context.session.refresh(result)
    return ApplicationData.model_validate(result)


@my_router.delete(
    "/{app_slug}",
    responses={**e404},
    response_model=ApplicationData,
    dependencies=[
        CoreSecurity("app:d"),
    ],
)
async def delete_app(context: ContextDep, app_slug: str):
    """Delete an existing application."""
    # Locate requested record.
    query = await context.session.execute(
        select(Application).where(Application.slug == app_slug)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        return no_app(app_slug)

    # Delete the record.
    await context.session.delete(result)
    await context.session.commit()
    return ApplicationData.model_validate(result)


router.include_router(my_router)
