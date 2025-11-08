from fastapi import APIRouter, HTTPException, status, Header
from services import guest_service
from config import settings
from typing import Optional

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/cleanup-expired-urls")
async def cleanup_expired_urls(x_admin_key: Optional[str] = Header(None)):
    """
    Cleanup expired guest URLs - Admin endpoint
    Requires X-Admin-Key header with SECRET_KEY
    Should be called by a cron job daily
    """
    # Simple authentication with admin key
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )
    
    deleted_count = await guest_service.cleanup_expired_urls()
    
    return {
        "message": "Cleanup completed",
        "deleted_urls": deleted_count
    }
