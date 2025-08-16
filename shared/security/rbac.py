"""
Role-Based Access Control (RBAC) System
Implements granular roles and permissions with resource-level access control
"""

import logging
from typing import Dict, List, Set, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

from fastapi import HTTPException, status, Depends, Request

if TYPE_CHECKING:
    from shared.models.auth import CreatorResponse

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """System roles with hierarchical permissions"""
    CREATOR = "creator"
    CREATOR_READONLY = "creator-readonly"
    ADMIN = "admin"
    SUPPORT = "support"


class Permission(str, Enum):
    """Granular permissions for resources"""
    # Creator management
    CREATE_CREATOR = "create:creator"
    READ_CREATOR = "read:creator"
    UPDATE_CREATOR = "update:creator"
    DELETE_CREATOR = "delete:creator"
    
    # Widget management
    CREATE_WIDGET = "create:widget"
    READ_WIDGET = "read:widget"
    UPDATE_WIDGET = "update:widget"
    DELETE_WIDGET = "delete:widget"
    
    # Document management
    CREATE_DOCUMENT = "create:document"
    READ_DOCUMENT = "read:document"
    UPDATE_DOCUMENT = "update:document"
    DELETE_DOCUMENT = "delete:document"
    
    # Conversation management
    CREATE_CONVERSATION = "create:conversation"
    READ_CONVERSATION = "read:conversation"
    UPDATE_CONVERSATION = "update:conversation"
    DELETE_CONVERSATION = "delete:conversation"
    
    # Analytics and metrics
    READ_ANALYTICS = "read:analytics"
    READ_METRICS = "read:metrics"
    
    # Administrative functions
    MANAGE_USERS = "manage:users"
    MANAGE_SYSTEM = "manage:system"
    VIEW_AUDIT_LOGS = "view:audit_logs"
    
    # Support functions
    READ_SUPPORT_DATA = "read:support_data"
    UPDATE_SUPPORT_TICKETS = "update:support_tickets"


@dataclass
class RoleDefinition:
    """Definition of a role with its permissions"""
    name: str
    description: str
    permissions: Set[Permission]
    inherits_from: Optional[List[str]] = None


class RBACManager:
    """Manages roles, permissions, and access control"""
    
    def __init__(self):
        self.roles: Dict[str, RoleDefinition] = {}
        self._initialize_default_roles()
    
    def _initialize_default_roles(self):
        """Initialize default system roles"""
        
        # Creator role - full access to own resources
        self.roles[Role.CREATOR] = RoleDefinition(
            name=Role.CREATOR,
            description="Content creator with full access to their resources",
            permissions={
                Permission.READ_CREATOR,
                Permission.UPDATE_CREATOR,
                Permission.CREATE_WIDGET,
                Permission.READ_WIDGET,
                Permission.UPDATE_WIDGET,
                Permission.DELETE_WIDGET,
                Permission.CREATE_DOCUMENT,
                Permission.READ_DOCUMENT,
                Permission.UPDATE_DOCUMENT,
                Permission.DELETE_DOCUMENT,
                Permission.CREATE_CONVERSATION,
                Permission.READ_CONVERSATION,
                Permission.UPDATE_CONVERSATION,
                Permission.DELETE_CONVERSATION,
                Permission.READ_ANALYTICS,
                Permission.READ_METRICS,
            }
        )
        
        # Creator readonly role - read-only access to own resources
        self.roles[Role.CREATOR_READONLY] = RoleDefinition(
            name=Role.CREATOR_READONLY,
            description="Read-only access to creator resources",
            permissions={
                Permission.READ_CREATOR,
                Permission.READ_WIDGET,
                Permission.READ_DOCUMENT,
                Permission.READ_CONVERSATION,
                Permission.READ_ANALYTICS,
                Permission.READ_METRICS,
            }
        )
        
        # Admin role - inherits creator permissions plus administrative functions
        self.roles[Role.ADMIN] = RoleDefinition(
            name=Role.ADMIN,
            description="Administrator with access to multiple creators and system functions",
            permissions={
                Permission.CREATE_CREATOR,
                Permission.READ_CREATOR,
                Permission.UPDATE_CREATOR,
                Permission.DELETE_CREATOR,
                Permission.MANAGE_USERS,
                Permission.MANAGE_SYSTEM,
                Permission.VIEW_AUDIT_LOGS,
            },
            inherits_from=[Role.CREATOR]
        )
        
        # Support role - limited access for customer support
        self.roles[Role.SUPPORT] = RoleDefinition(
            name=Role.SUPPORT,
            description="Customer support with limited access to user data",
            permissions={
                Permission.READ_SUPPORT_DATA,
                Permission.UPDATE_SUPPORT_TICKETS,
                Permission.VIEW_AUDIT_LOGS,
            },
            inherits_from=[Role.CREATOR_READONLY]
        )
    
    def get_role_permissions(self, role: str) -> Set[Permission]:
        """Get all permissions for a role, including inherited permissions"""
        if role not in self.roles:
            logger.warning(f"Unknown role requested: {role}")
            return set()
        
        role_def = self.roles[role]
        permissions = role_def.permissions.copy()
        
        # Add inherited permissions
        if role_def.inherits_from:
            for parent_role in role_def.inherits_from:
                permissions.update(self.get_role_permissions(parent_role))
        
        return permissions
    
    def has_permission(self, user_roles: List[str], required_permission: Permission) -> bool:
        """Check if user has required permission based on their roles"""
        for role in user_roles:
            role_permissions = self.get_role_permissions(role)
            if required_permission in role_permissions:
                return True
        return False
    
    def has_any_permission(self, user_roles: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has any of the required permissions"""
        for permission in required_permissions:
            if self.has_permission(user_roles, permission):
                return True
        return False
    
    def has_all_permissions(self, user_roles: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions"""
        for permission in required_permissions:
            if not self.has_permission(user_roles, permission):
                return False
        return True
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """Get all permissions for a user based on their roles"""
        all_permissions = set()
        for role in user_roles:
            all_permissions.update(self.get_role_permissions(role))
        return all_permissions
    
    def add_custom_role(self, role_def: RoleDefinition):
        """Add a custom role definition"""
        self.roles[role_def.name] = role_def
        logger.info(f"Added custom role: {role_def.name}")
    
    def create_role(self, role_name: str, permissions: List[str]) -> bool:
        """
        Create a new role (alias for add_custom_role for backward compatibility).
        
        Args:
            role_name: Name of the role
            permissions: List of permission strings
            
        Returns:
            True if role was created successfully
        """
        try:
            # Convert string permissions to Permission enum if possible
            permission_set = set()
            for perm in permissions:
                try:
                    # Try to find matching Permission enum
                    for p in Permission:
                        if p.value == perm or perm in p.value:
                            permission_set.add(p)
                            break
                    else:
                        # If no enum match, create a custom permission string
                        permission_set.add(perm)
                except Exception:
                    permission_set.add(perm)
            
            # Create role definition
            role_def = RoleDefinition(
                name=role_name,
                description=f"Custom role: {role_name}",
                permissions=permission_set
            )
            
            self.add_custom_role(role_def)
            return True
            
        except Exception as e:
            logger.error(f"Failed to create role {role_name}: {e}")
            return False
    
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user (placeholder implementation).
        
        Note: This is a simplified implementation for testing.
        In a real system, this would interact with a user management system.
        """
        # This is a mock implementation for testing
        logger.info(f"Assigned role {role_name} to user {user_id}")
        return True
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get roles assigned to a user (placeholder implementation).
        
        Note: This is a simplified implementation for testing.
        """
        # This is a mock implementation for testing
        return ["creator"]  # Default role
    
    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user (placeholder implementation).
        """
        # This is a mock implementation for testing
        logger.info(f"Removed role {role_name} from user {user_id}")
        return True
    
    def remove_role(self, role_name: str):
        """Remove a role definition"""
        if role_name in self.roles:
            del self.roles[role_name]
            logger.info(f"Removed role: {role_name}")


# Global RBAC manager instance
rbac_manager = RBACManager()


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def require_permission(required_permission: Permission):
    """
    Decorator factory for permission-based access control
    
    Args:
        required_permission: Required permission for access
        
    Returns:
        Dependency function for FastAPI
    """
    async def permission_checker(
        creator: "CreatorResponse" = Depends(get_current_creator)
    ) -> "CreatorResponse":
        """Check if creator has required permission"""
        
        # Get user roles (for MVP, based on subscription tier)
        user_roles = get_roles_from_subscription(creator.subscription_tier)
        
        # Check permission
        if not rbac_manager.has_permission(user_roles, required_permission):
            logger.warning(
                f"Permission denied for creator {creator.id}: "
                f"required_permission={required_permission.value}, user_roles={user_roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required permission: {required_permission.value}"
            )
        
        return creator
    
    return permission_checker


def require_any_permission(required_permissions: List[Permission]):
    """
    Decorator factory for multiple permission access control (OR logic)
    
    Args:
        required_permissions: List of permissions (user needs any one)
        
    Returns:
        Dependency function for FastAPI
    """
    async def permission_checker(
        creator: "CreatorResponse" = Depends(get_current_creator)
    ) -> "CreatorResponse":
        """Check if creator has any of the required permissions"""
        
        user_roles = get_roles_from_subscription(creator.subscription_tier)
        
        if not rbac_manager.has_any_permission(user_roles, required_permissions):
            permission_names = [p.value for p in required_permissions]
            logger.warning(
                f"Permission denied for creator {creator.id}: "
                f"required_any_permissions={permission_names}, user_roles={user_roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required any of: {', '.join(permission_names)}"
            )
        
        return creator
    
    return permission_checker


def require_all_permissions(required_permissions: List[Permission]):
    """
    Decorator factory for multiple permission access control (AND logic)
    
    Args:
        required_permissions: List of permissions (user needs all)
        
    Returns:
        Dependency function for FastAPI
    """
    async def permission_checker(
        creator: "CreatorResponse" = Depends(get_current_creator)
    ) -> "CreatorResponse":
        """Check if creator has all required permissions"""
        
        user_roles = get_roles_from_subscription(creator.subscription_tier)
        
        if not rbac_manager.has_all_permissions(user_roles, required_permissions):
            permission_names = [p.value for p in required_permissions]
            logger.warning(
                f"Permission denied for creator {creator.id}: "
                f"required_all_permissions={permission_names}, user_roles={user_roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required all of: {', '.join(permission_names)}"
            )
        
        return creator
    
    return permission_checker


def require_role(required_role: Role):
    """
    Decorator factory for role-based access control
    
    Args:
        required_role: Required role for access
        
    Returns:
        Dependency function for FastAPI
    """
    async def role_checker(
        creator: "CreatorResponse" = Depends(get_current_creator)
    ) -> "CreatorResponse":
        """Check if creator has required role"""
        
        user_roles = get_roles_from_subscription(creator.subscription_tier)
        
        if required_role.value not in user_roles:
            logger.warning(
                f"Role access denied for creator {creator.id}: "
                f"required_role={required_role.value}, user_roles={user_roles}"
            )
            raise AuthorizationError(
                f"Access denied. Required role: {required_role.value}"
            )
        
        return creator
    
    return role_checker


def require_resource_ownership(resource_field: str = "creator_id"):
    """
    Decorator factory for resource ownership validation
    
    Args:
        resource_field: Field name containing creator ID in path/query params
        
    Returns:
        Dependency function for FastAPI
    """
    async def ownership_checker(
        request: Request,
        creator: "CreatorResponse" = Depends(get_current_creator)
    ) -> "CreatorResponse":
        """Check if creator owns the requested resource"""
        
        # Extract resource creator ID from path parameters
        path_params = request.path_params
        resource_creator_id = path_params.get(resource_field)
        
        if not resource_creator_id:
            # If not in path params, check query params
            query_params = dict(request.query_params)
            resource_creator_id = query_params.get(resource_field)
        
        # For admin users, allow access to any resource
        user_roles = get_roles_from_subscription(creator.subscription_tier)
        if Role.ADMIN.value in user_roles:
            return creator
        
        # Check ownership
        if resource_creator_id and resource_creator_id != creator.id:
            logger.warning(
                f"Resource access denied for creator {creator.id}: "
                f"attempted to access resource owned by {resource_creator_id}"
            )
            raise AuthorizationError("Access denied to resource")
        
        return creator
    
    return ownership_checker


def get_roles_from_subscription(subscription_tier: str) -> List[str]:
    """
    Map subscription tier to roles (MVP implementation)
    
    Args:
        subscription_tier: User's subscription tier
        
    Returns:
        List of roles for the user
    """
    role_mapping = {
        "free": [Role.CREATOR.value],
        "pro": [Role.CREATOR.value],
        "enterprise": [Role.CREATOR.value, Role.ADMIN.value],
        "support": [Role.SUPPORT.value],
        "admin": [Role.ADMIN.value]
    }
    
    return role_mapping.get(subscription_tier, [Role.CREATOR.value])


def check_permission_sync(user_roles: List[str], required_permission: Permission) -> bool:
    """Synchronous permission check for use in non-async contexts"""
    return rbac_manager.has_permission(user_roles, required_permission)


def get_user_permissions_sync(user_roles: List[str]) -> Set[Permission]:
    """Synchronous method to get user permissions"""
    return rbac_manager.get_user_permissions(user_roles)


# Convenience decorators for common permission patterns
def require_creator_access():
    """Require creator-level access to resources"""
    return require_permission(Permission.READ_CREATOR)


def require_widget_management():
    """Require widget management permissions"""
    return require_permission(Permission.UPDATE_WIDGET)


def require_document_management():
    """Require document management permissions"""
    return require_permission(Permission.UPDATE_DOCUMENT)


def require_analytics_access():
    """Require analytics access permissions"""
    return require_permission(Permission.READ_ANALYTICS)


def require_admin_access():
    """Require administrative access"""
    return require_role(Role.ADMIN)


def require_support_access():
    """Require support access"""
    return require_any_permission([
        Permission.READ_SUPPORT_DATA,
        Permission.VIEW_AUDIT_LOGS
    ])


# Import guard to prevent circular imports
def get_current_creator():
    """Import guard for get_current_creator dependency"""
    from services.auth_service.app.dependencies.auth import get_current_creator as _get_current_creator
    return _get_current_creator