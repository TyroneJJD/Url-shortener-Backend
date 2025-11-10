from fastapi import APIRouter, HTTPException, status, Depends, Response, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from models import URLCreate, URLUpdate, URLResponse, User, URLBulkCreate, URLAccessHistory
from services import url_service, guest_service
from services.auth_service import registered_user_service
from services.base_user_service import BaseUserService
from middleware import get_current_user_from_cookie, get_optional_user_from_cookie
from config import settings
import json
from io import BytesIO
from datetime import datetime, timezone

router = APIRouter(tags=["URLs"])


def get_user_service(user_type: str) -> BaseUserService:
    """
    Helper function to get the appropriate user service based on user type
    """
    return guest_service if user_type == 'guest' else registered_user_service


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
            
            return response
        
        # Guest users cannot access private URLs (only registered users)
        if current_user.user_type == 'guest':
            return Response(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": f"{settings.FRONTEND_URL}/{short_code}?error=guest_forbidden"}
            )
        
        # Record access for authenticated users accessing private URLs
        if current_user and current_user.email:
            await url_service.record_url_access(url.id, current_user.email, current_user.user_type)
    
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
    Registered users: limited to 100 URLs, no expiration, can create private URLs
    """
    # Guest users cannot create private URLs
    if current_user.user_type == 'guest' and url_data.is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot create private URLs. Please register to use this feature."
        )
    
    # Get appropriate user service and check if user can create URL
    user_service = get_user_service(current_user.user_type)
    can_create = await user_service.can_create_url(current_user.id)
    
    if not can_create:
        detail_msg = f"{'Guest users' if current_user.user_type == 'guest' else 'Registered users'} can only create {user_service.max_urls} URLs."
        if current_user.user_type == 'guest':
            detail_msg += " Please register for more URLs."
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg
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
async def get_my_urls(
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    with_history: bool = Query(False, description="Include access history for each URL"),
    export: bool = Query(False, description="Export all URLs as JSON file"),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get URLs created by current user with pagination - Requires Cookie Auth
    Supports pagination (offset/limit) and optional access history
    Returns total count for frontend pagination calculations
    
    If export=true, ignores pagination and returns all URLs as downloadable JSON file
    
    """
    
    # If export mode, get all URLs without pagination
    if export:
        return await get_as_file(current_user, with_history, offset)
    
    # Normal pagination mode
    return await get_as_json(current_user, with_history, offset)


async def get_as_file(current_user: User, with_history: bool, offset: int = 0):
    """
    Helper function to export URLs as file
    """
    # Get ALL URLs (pagination, fixed large limit)
    total, urls = await url_service.get_user_urls(current_user.id, offset, with_history)

    # Build export data
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": current_user.id,
        "username": current_user.username,
        "total_urls": total,
        "urls": []
    }
    
    for url in urls:
        url_dict = {
            "id": url.id,
            "short_code": url.short_code,
            "original_url": url.original_url,
            "clicks": url.clicks,
            "is_active": url.is_active,
            "is_private": url.is_private,
            "created_at": url.created_at.isoformat(),
            "expires_at": url.expires_at.isoformat() if url.expires_at else None
        }

        print(url_dict)
        
        # Add access history if requested
        if with_history and hasattr(url, 'access_history'):
            url_dict["access_history"] = [
                {
                    "user_email": h["user_email"],
                    "user_type": h["user_type"],
                    "accessed_at": h["accessed_at"].isoformat()
                }
                for h in url.access_history
            ]
        
        export_data["urls"].append(url_dict)
    
    # Convert to JSON and create file
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    json_bytes = BytesIO(json_str.encode('utf-8'))
    
    # Generate filename with timestamp
    filename = f"urls_export_{current_user.username}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    # Return as downloadable file
    return StreamingResponse(
        json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


async def get_as_json(current_user: User, with_history: bool, offset: int = 0):
    """
    Helper function to return URLs as JSON response with pagination
    """
    # Get paginated URLs
    total, urls = await url_service.get_user_urls(current_user.id,offset,with_history)
    
    response_urls = []
    for url in urls:
        url_response = URLResponse(
            id=url.id,
            short_code=url.short_code,
            original_url=url.original_url,
            clicks=url.clicks,
            is_active=url.is_active,
            is_private=url.is_private,
            created_at=url.created_at,
            expires_at=url.expires_at
        )
        
        # Add access history if requested and available
        if with_history and hasattr(url, 'access_history'):
            url_response.access_history = [
                URLAccessHistory(**history) for history in url.access_history
            ]
        
        response_urls.append(url_response)
    
    return {
        "total": total,
        "offset": offset,
        "urls": response_urls
    }



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


@router.post("/urls/bulk")
async def create_urls_bulk(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Create multiple shortened URLs from JSON file - Requires Cookie Auth
    
    JSON format: {"urls": [{"url": "https://example.com", "is_private": false}, ...]}
    
    Guest users: 
    - Limited to 5 total URLs (existing + new)
    - Cannot create private URLs
    - URLs expire in 7 days
    
    Registered users: 
    - Max 100 URLs (total)
    - Can create private URLs
    - No expiration

    Max 100 URLs per request
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file"
        )
    
    try:
        # Read and parse JSON file
        content = await file.read()
        data = json.loads(content)
        
        # Validate using Pydantic model
        bulk_data = URLBulkCreate(**data)
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if any URL is private and user is guest
    if current_user.user_type == 'guest':
        if any(url_item.is_private for url_item in bulk_data.urls):
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest users cannot create private URLs. Please register to use this feature."
            )
        
    # Get appropriate user service
    user_service = get_user_service(current_user.user_type)
    
    # Get remaining URL slots
    remaining_urls = await user_service.get_remaining_urls(current_user.id)
    urls_to_create = len(bulk_data.urls)
    
    # Check if user would exceed their limit
    if remaining_urls is not None and urls_to_create > remaining_urls:
        current_count = await user_service.get_url_count(current_user.id)
        user_type_label = 'Guest users' if current_user.user_type == 'guest' else 'Registered users'
        detail_msg = f"{user_type_label} can only create {user_service.max_urls} URLs total. "
        detail_msg += f"You have {current_count} URLs and are trying to create {urls_to_create} more."
        if current_user.user_type == 'guest':
            detail_msg += " Please register for more URLs."
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_msg
        )
    
    
    # Prepare data for bulk creation
    urls_data = [(url_item.url, url_item.is_private) for url_item in bulk_data.urls]
    
    # Create URLs in bulk
    created_urls = await url_service.create_urls_bulk(urls_data, current_user.id, current_user.user_type)
    
    # Return created URLs
    return {
        "message": f"Successfully created {len(created_urls)} URLs",
        "urls": [
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
            for url in created_urls
        ]
    }
