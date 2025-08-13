from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("pseudonym", "klassengruppe", "gruppe", "created_at")
    list_filter = ("klassengruppe", "gruppe")
    search_fields = ("pseudonym",)
