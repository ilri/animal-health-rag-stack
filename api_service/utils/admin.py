import os
from typing import Optional
from fastapi import Request, HTTPException

class AdminManager:
    """Simple admin mode manager for controlling access to destructive operations."""
    
    def __init__(self):
        # Allow admin mode to be enabled via environment variable
        self.admin_enabled = os.getenv('ENABLE_ADMIN_MODE', 'true').lower() == 'true'
        # Admin password/token (optional for additional security)
        self.admin_token = os.getenv('ADMIN_TOKEN', '')
    
    def is_admin_request(self, request: Request) -> bool:
        """
        Check if the request is from an admin user.
        
        Admin access can be granted through:
        1. Query parameter: ?admin=true (if ENABLE_ADMIN_MODE is true)
        2. Query parameter: ?admin=<token> (if ADMIN_TOKEN is set)
        3. Header: X-Admin-Mode: true (if ENABLE_ADMIN_MODE is true)
        4. Header: X-Admin-Token: <token> (if ADMIN_TOKEN is set)
        """
        # Check environment-based admin mode
        if self.admin_enabled:
            # Check query parameter
            if request.query_params.get('admin') == 'true':
                return True
            
            # Check header
            if request.headers.get('x-admin-mode') == 'true':
                return True
        
        # Check token-based admin mode
        if self.admin_token:
            # Check query parameter token
            if request.query_params.get('admin') == self.admin_token:
                return True
            
            # Check header token
            if request.headers.get('x-admin-token') == self.admin_token:
                return True
        
        return False
    
    def require_admin(self, request: Request, operation_name: str = "operation"):
        """
        Require admin access for an operation.
        Raises HTTPException if not admin.
        """
        if not self.is_admin_request(request):
            raise HTTPException(
                status_code=403, 
                detail=f"Admin access required for {operation_name}. Enable admin mode or provide admin token."
            )
    
    def get_admin_info(self) -> dict:
        """Get information about admin mode configuration."""
        return {
            "admin_mode_enabled": self.admin_enabled,
            "token_auth_configured": bool(self.admin_token),
            "access_methods": {
                "query_param": "?admin=true" if self.admin_enabled else "?admin=<token>",
                "header": "X-Admin-Mode: true" if self.admin_enabled else "X-Admin-Token: <token>"
            }
        }

# Global admin manager instance
admin_manager = AdminManager()