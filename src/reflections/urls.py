from django.urls import path
from .views import ReflectionCreateView, NoteCreateView, NextStepSuggestView

urlpatterns = [
    path('reflections/', ReflectionCreateView.as_view()),
    path('notes/', NoteCreateView.as_view()),
    path('vg/next-step/suggest/', NextStepSuggestView.as_view()),
]
