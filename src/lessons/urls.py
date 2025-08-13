from django.urls import path
from .views import LessonSessionCreateView, UserSessionEnterView

urlpatterns = [
    path('lessons/', LessonSessionCreateView.as_view()),
    path('user-sessions/enter/', UserSessionEnterView.as_view()),
]
