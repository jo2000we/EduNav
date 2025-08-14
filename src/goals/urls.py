from django.urls import path
from .views import (
    GoalCreateKGView,
    GoalCreateVGView,
    CoachNextView,
    GoalFinalizeView,
    OverallGoalView,
)

urlpatterns = [
    path('goals/', GoalCreateKGView.as_view()),
    path('vg/goals/', GoalCreateVGView.as_view()),
    path('vg/coach/next/', CoachNextView.as_view()),
    path('vg/goals/finalize/', GoalFinalizeView.as_view()),
    path('overall-goal/', OverallGoalView.as_view()),
]
