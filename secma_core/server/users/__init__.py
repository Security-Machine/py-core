from fastapi import APIRouter, Depends

from secma_core.server.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/users/{app_slug}/{tn_slug}",
    dependencies=[Depends(get_current_user)],
)
