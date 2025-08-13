from django.urls import path
from .views import ExportCSVView, ExportXLSXView

urlpatterns = [
    path('export/csv/', ExportCSVView.as_view()),
    path('export/xlsx/', ExportXLSXView.as_view()),
]
