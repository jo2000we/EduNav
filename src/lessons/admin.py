from django.contrib import admin
from .models import LessonSession, UserSession

@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "topic", "period", "use_ai")
    list_filter = ("date", "use_ai")

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson_session", "started_at")
    list_filter = ("lesson_session",)
