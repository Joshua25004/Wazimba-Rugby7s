from rest_framework.permissions import SAFE_METHODS, BasePermission


def app_role(user):
    if not user or not user.is_authenticated:
        return None
    from .models import UserProfile
    try: return user.team_profile.role
    except UserProfile.DoesNotExist: pass
    role = UserProfile.Role.ADMINISTRATOR if user.is_superuser else UserProfile.Role.STAFF if user.is_staff else UserProfile.Role.MEMBER
    return UserProfile.objects.get_or_create(user=user, defaults={'role': role})[0].role


def has_welfare_access(user):
    if not user or not user.is_authenticated:
        return False
    from .models import UserProfile
    role = app_role(user)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return role in (UserProfile.Role.STAFF, UserProfile.Role.ADMINISTRATOR) and profile.can_access_welfare


class ReadOnlyOrStaff(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        from .models import UserProfile
        return app_role(request.user) in (UserProfile.Role.STAFF, UserProfile.Role.ADMINISTRATOR)


class WelfareStaffOnly(BasePermission):
    def has_permission(self, request, view):
        return has_welfare_access(request.user)


class AdministratorOnly(BasePermission):
    def has_permission(self, request, view):
        from .models import UserProfile
        return bool(request.user and request.user.is_authenticated and app_role(request.user) == UserProfile.Role.ADMINISTRATOR)
