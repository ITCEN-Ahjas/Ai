from fastapi import APIRouter

from app.api.v1.endpoints import chat, outfit

router = APIRouter(prefix="/api/v1")

router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(outfit.router, prefix="/outfits", tags=["outfits"])