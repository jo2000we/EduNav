from django.contrib import admin
from .models import Classroom, Student, LearningGoal

class StudentInline(admin.TabularInline):
    model = Student
    extra = 1

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "teacher",
        "group_type",
        "max_entries_per_day",
        "max_entries_per_week",
    )
    list_filter = ("group_type",)
    inlines = [StudentInline]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("pseudonym", "classroom")
    search_fields = ("pseudonym",)

@admin.register(LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ("student", "session_date", "achieved")
    list_filter = ("achieved", "session_date")
