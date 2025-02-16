from fastapi import APIRouter
from core.settings import settings
from .users import router as users_router
from .transactions import router as transactions_router

router = APIRouter()

router.include_router(
    users_router
)

router.include_router(
     transactions_router
)