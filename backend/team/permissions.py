from rest_framework.permissions import SAFE_METHODS, BasePermission

class ReadOnlyOrStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.method in SAFE_METHODS or request.user.is_staff))

class WelfareStaffOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
