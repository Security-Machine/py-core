from fastapi import APIRouter, Depends

from secma_core.server.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/mng",
    tags=["Instance Management"],
)
