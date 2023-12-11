from typing import Annotated

from fastapi import Depends, Path, Request
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from sqlalchemy.orm.exc import NoResultFound

from secma_core.db.models.application import Application
from secma_core.server.utils import no_app


async def get_app_id(
    request: Request,
    app_slug: str = Path(
        ...,
        title="The slug of the application.",
        description=(
            "This needs to be a non-empty, lower case, alpa-numeric string. "
        ),
    ),
) -> int:
    """Get the application from path.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        app_slug: The value provided in the url.

    Returns:
        The application ID.
    """

    query = await request.state.session.execute(
        select(Application)
        .options(load_only(Application.id))
        .where(Application.slug == app_slug)
    )
    try:
        result = query.scalar_one()
    except NoResultFound:
        raise no_app(app_slug, mode="html")

    return result.id


AppIdArg = Annotated[int, Depends(get_app_id)]


async def get_app_slug(
    app_slug: str = Path(
        ...,
        title="The slug of the application.",
        description=(
            "This needs to be a non-empty, lower case, alpa-numeric string. "
        ),
    ),
) -> str:
    """Get the application slug from path.

    This is a dependency that can be used in FastAPI endpoints.

    Args:
        app_slug: The value provided in the url.

    Returns:
        The application slug.
    """
    return app_slug


AppSlugArg = Annotated[str, Depends(get_app_slug)]
