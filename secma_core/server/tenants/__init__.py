from fastapi import APIRouter, Depends

from secma_core.server.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/tenants/{app_slug}",
    tags=["Tenant Management"],
    dependencies=[Depends(get_current_user)],
)
