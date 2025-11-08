from fastapi import APIRouter, HTTPException, status, Depends, Response
from typing import List
from models import URLCreate, URLUpdate, URLResponse, User
from services import url_service, guest_service
from middleware import get_current_user_from_cookie, get_optional_user_from_cookie
from config import settings

router = APIRouter(tags=["URLs"])


@router.get("/{short_code}")
async def resolve_url(short_code: str, current_user: User = Depends(get_optional_user_from_cookie)):
    """
    Resolve short URL and redirect - Public (unless URL is private)
    Returns 301 redirect to original URL
    If URL is private or not found, redirects to frontend for error handling
    Guest users cannot access private URLs (only registered users)
    """
    url = await url_service.get_url_by_short_code(short_code)
    
    if not url:
        # Redirect to frontend with 404 status
        return Response(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": f"{settings.FRONTEND_URL}/{short_code}?error=not_found"}
        )
    
    # Check if URL is private - guests and non-authenticated users cannot access
    if url.is_private:
        # Not authenticated at all
        if not current_user:
            # Save short_code in cookie for post-login redirect
            response = Response(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": f"{settings.FRONTEND_URL}/{short_code}?error=unauthorized"}
            )
            response.set_cookie(
                key="redirect_after_login",
                value=short_code,
                httponly=True,
                max_age=300,  # 5 minutes
                samesite="lax"
            )
            return response
        
        # Guest users cannot access private URLs (only registered users)
        if current_user.user_type == 'guest':
            return Response(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": f"{settings.FRONTEND_URL}/{short_code}?error=guest_forbidden"}
            )
    
    # Increment click counter
    await url_service.increment_clicks(short_code)
    
    # Return 301 redirect to original URL
    return Response(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={"Location": url.original_url}
    )


@router.post("/urls")
async def create_url(
    url_data: URLCreate,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Create a shortened URL - Requires Cookie Auth
    Guest users: limited to 5 URLs, expire in 7 days, cannot create private URLs
    Registered users: unlimited URLs, no expiration, can create private URLs
    """
    # Guest users cannot create private URLs
    if current_user.user_type == 'guest' and url_data.is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot create private URLs. Please register to use this feature."
        )
    
    # Check if user can create URL (guest limit)
    can_create = await guest_service.can_create_url(current_user.id, current_user.user_type)
    
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users can only create 5 URLs. Please register for unlimited URLs."
        )
    
    url = await url_service.create_url(url_data, current_user.id, current_user.user_type)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create URL"
        )
    
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        clicks=url.clicks,
        is_active=url.is_active,
        is_private=url.is_private,
        created_at=url.created_at,
        expires_at=url.expires_at
    )


@router.get("/urls/me/all")
async def get_my_urls(current_user: User = Depends(get_current_user_from_cookie)):
    """
    Get all URLs created by current user - Requires Cookie Auth
    """
    urls = await url_service.get_user_urls(current_user.id)
    
    return [
        URLResponse(
            id=url.id,
            short_code=url.short_code,
            original_url=url.original_url,
            clicks=url.clicks,
            is_active=url.is_active,
            is_private=url.is_private,
            created_at=url.created_at,
            expires_at=url.expires_at
        )
        for url in urls
    ]


@router.put("/urls/{url_id}")
async def edit_url(
    url_id: int,
    url_data: URLUpdate,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Edit a URL - Requires Cookie Auth
    Only the owner can edit the URL
    Guest users cannot set URLs as private
    """
    # Guest users cannot set URLs as private
    if current_user.user_type == 'guest' and url_data.is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot create private URLs. Please register to use this feature."
        )
    
    url = await url_service.update_url(url_id, current_user.id, url_data)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found or you don't have permission to edit it"
        )
    
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        clicks=url.clicks,
        is_active=url.is_active,
        is_private=url.is_private,
        created_at=url.created_at,
        expires_at=url.expires_at
    )


@router.delete("/urls/{url_id}")
async def delete_url(
    url_id: int,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Delete a URL - Requires Cookie Auth
    Only the owner can delete the URL
    """
    success = await url_service.delete_url(url_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found or you don't have permission to delete it"
        )
    
    return {"message": "URL deleted successfully"}
