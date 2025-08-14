from django.contrib import admin

from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin interface for the singleton SiteSettings model."""

    def has_add_permission(self, request):
        # Prevent creation of multiple instances
        return not SiteSettings.objects.exists() and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff
