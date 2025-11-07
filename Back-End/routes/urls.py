from fastapi import APIRouter, HTTPException, status, Depends, Response
from typing import List
from models import URLCreate, URLUpdate, URLResponse, User
from services import url_service
from middleware import get_current_user_from_cookie, get_optional_user_from_cookie

router = APIRouter(tags=["URLs"])


@router.get("/{short_code}")
async def resolve_url(short_code: str, current_user: User = Depends(get_optional_user_from_cookie)):
    """
    Resolve short URL and redirect - Public (unless URL is private)
    Returns 301 redirect to original URL
    If URL is private, requires authentication
    """
    url = await url_service.get_url_by_short_code(short_code)
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found"
        )
    
    # Check if URL is private and user is not authenticated
    if url.is_private and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this private URL"
        )
    
    # Increment click counter
    await url_service.increment_clicks(short_code)
    
    # Return 301 redirect
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
    """
    url = await url_service.create_url(url_data, current_user.id)
    
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
        created_at=url.created_at
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
            created_at=url.created_at
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
    """
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
        created_at=url.created_at
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
