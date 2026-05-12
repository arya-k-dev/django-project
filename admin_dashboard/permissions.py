from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class ForbiddenBasicAuthentication(BasicAuthentication):
    """Allow Basic auth credentials without returning 401 challenges."""

    def authenticate_header(self, request):
        return None


class ForbiddenSessionAuthentication(SessionAuthentication):
    """Keep unauthenticated admin API requests as 403 responses."""

    def authenticate_header(self, request):
        return None


def user_has_admin_access(user):
    """Return True only for authenticated users explicitly marked as admins."""
    if not getattr(user, 'is_authenticated', False):
        return False
    if not getattr(user, 'is_active', False):
        return False

    if getattr(user, 'is_admin', False):
        return True

    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return False

    return bool(profile and profile.is_admin)


class IsSkillSphereAdmin(BasePermission):
    """Server-side guard for every custom admin endpoint."""

    message = 'You do not have permission to access the admin dashboard.'

    def has_permission(self, request, view):
        if not user_has_admin_access(request.user):
            raise PermissionDenied(self.message)
        return True
