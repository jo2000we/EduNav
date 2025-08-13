from rest_framework.permissions import BasePermission

class IsVGUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "gruppe", "") == "VG"
