# accounts/tests.py
# Tests for registration, login, token refresh, and /me endpoint.
# Tests hit the full HTTP stack using DRF's APIClient.

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(db):
    return User.objects.create_user(
        email='test@example.com',
        password='strongpass99',
        full_name='Test User',
    )


# ── Registration ─────────────────────────────────────────────

@pytest.mark.django_db
def test_register_success(client):
    res = client.post('/api/auth/register/', {
        'email': 'new@example.com',
        'password': 'strongpass99',
        'full_name': 'New User',
    })
    assert res.status_code == 201
    assert 'tokens' in res.data
    assert res.data['user']['email'] == 'new@example.com'


@pytest.mark.django_db
def test_register_duplicate_email(client, registered_user):
    res = client.post('/api/auth/register/', {
        'email': 'test@example.com',
        'password': 'strongpass99',
    })
    assert res.status_code == 400


@pytest.mark.django_db
def test_register_short_password(client):
    res = client.post('/api/auth/register/', {
        'email': 'user@example.com',
        'password': '123',
    })
    assert res.status_code == 400


# ── Login ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_login_success(client, registered_user):
    res = client.post('/api/auth/login/', {
        'email': 'test@example.com',
        'password': 'strongpass99',
    })
    assert res.status_code == 200
    assert 'access' in res.data['tokens']
    assert 'refresh' in res.data['tokens']


@pytest.mark.django_db
def test_login_wrong_password(client, registered_user):
    res = client.post('/api/auth/login/', {
        'email': 'test@example.com',
        'password': 'wrongpassword',
    })
    assert res.status_code == 401


@pytest.mark.django_db
def test_login_nonexistent_user(client):
    res = client.post('/api/auth/login/', {
        'email': 'nobody@example.com',
        'password': 'whatever123',
    })
    assert res.status_code == 401


# ── Me endpoint ───────────────────────────────────────────────

@pytest.mark.django_db
def test_me_authenticated(client, registered_user):
    login = client.post('/api/auth/login/', {
        'email': 'test@example.com',
        'password': 'strongpass99',
    })
    token = login.data['tokens']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    res = client.get('/api/auth/me/')
    assert res.status_code == 200
    assert res.data['email'] == 'test@example.com'


@pytest.mark.django_db
def test_me_unauthenticated(client):
    res = client.get('/api/auth/me/')
    assert res.status_code == 401