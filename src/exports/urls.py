from django.urls import path
from .views import ExportCSVView, ExportXLSXView, DashboardDataView

app_name = "exports"

urlpatterns = [
    path('export/csv/', ExportCSVView.as_view(), name="csv"),
    path('export/xlsx/', ExportXLSXView.as_view(), name="xlsx"),
    path('export/dashboard-data/', DashboardDataView.as_view(), name="dashboard-data"),
]
