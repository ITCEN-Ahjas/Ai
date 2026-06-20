from fastapi import APIRouter
from app.api.v1.endpoints import chat

router = APIRouter(prefix="/api/v1")
router.include_router(chat.router, prefix="/chat", tags=["chat"])
