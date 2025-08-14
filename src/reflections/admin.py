from django.contrib import admin
from .models import Reflection


@admin.register(Reflection)
class ReflectionAdmin(admin.ModelAdmin):
    list_display = ("user_session", "goal", "result", "created_at")
    list_filter = ("result",)
