from django.contrib import admin
from .models import Goal, KIInteraction, OverallGoal

class KIInteractionInline(admin.TabularInline):
    model = KIInteraction
    extra = 0

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("user_session", "raw_text", "final_text", "finalized_at")
    inlines = [KIInteractionInline]


@admin.register(OverallGoal)
class OverallGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "created_at")
