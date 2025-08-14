from django.contrib import admin
from .models import LessonSession, UserSession, Classroom

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "use_ai")
    search_fields = ("name", "code")

@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = ("date", "topic", "period", "classroom", "use_ai")
    list_filter = ("date", "classroom", "use_ai")

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson_session", "started_at")
    list_filter = ("lesson_session",)
