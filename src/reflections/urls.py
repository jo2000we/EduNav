from django.urls import path
from .views import ReflectionCreateView, NextStepSuggestView

urlpatterns = [
    path('reflections/', ReflectionCreateView.as_view()),
    path('vg/next-step/suggest/', NextStepSuggestView.as_view()),
]
