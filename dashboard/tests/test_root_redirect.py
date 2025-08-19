import pytest

@pytest.mark.django_db
def test_root_redirects_to_student_dashboard(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == "/student/dashboard/"

