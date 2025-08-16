from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def export_classroom_data(request, classroom_id):
    """Placeholder view for exporting classroom data."""
    return HttpResponse("Export interface not implemented yet.")
