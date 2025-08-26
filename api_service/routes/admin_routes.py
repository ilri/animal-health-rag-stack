from fastapi import APIRouter, Request
from utils.admin import admin_manager

router = APIRouter()

@router.get("/admin/status")
async def get_admin_status(request: Request):
    """Check if the current request has admin access."""
    is_admin = admin_manager.is_admin_request(request)
    return {
        "status": "success",
        "is_admin": is_admin,
        **admin_manager.get_admin_info()
    }

@router.get("/admin/info")
async def get_admin_info():
    """Get information about admin mode configuration."""
    return {
        "status": "success",
        **admin_manager.get_admin_info()
    }