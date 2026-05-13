# First test — verifies the health endpoint works.

import pytest
from rest_framework.test import APIClient

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_health_check(client):
    response = client.get('/api/health/')
    assert response.status_code == 200
    assert response.data['status'] == 'ok'