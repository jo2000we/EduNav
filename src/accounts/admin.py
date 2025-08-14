from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("pseudonym", "classroom", "gruppe", "created_at")
    list_filter = ("classroom", "gruppe")
    search_fields = ("pseudonym",)
