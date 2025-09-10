from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Only admin users can access"""
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.role == 'admin')


class IsAdminOrManager(permissions.BasePermission):
    """Admin and Manager users can access"""
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.role in ['admin', 'manager'])


class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Admin and Manager have full access.
    Others have read-only access.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.role in ['admin', 'manager']


class IsOwnerOrAdminOrManager(permissions.BasePermission):
    """
    Object-level permission to only allow owners, admin, or managers
    to edit objects.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'manager']:
            return True
        
        # Check if obj has an owner field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False