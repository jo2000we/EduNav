from django.urls import path
from .views import LoginView, MeView

urlpatterns = [
    path('login/', LoginView.as_view(), name='api-login'),
    path('me/', MeView.as_view(), name='me'),
]
