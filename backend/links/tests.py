# links/tests.py
# Tests for: short code generation, link creation, list,
# detail, update, delete, redirect, anonymous shortening.

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from links.models import Link
from links.short_code import ShortCodeService, encode_base62, decode_base62
from links.services import LinkService

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='owner@example.com',
        password='strongpass99',
    )


@pytest.fixture
def auth_client(client, user):
    res = client.post('/api/auth/login/', {
        'email': 'owner@example.com',
        'password': 'strongpass99',
    })
    token = res.data['tokens']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def link(db, user):
    return LinkService.create_link(
        original_url='https://example.com/very/long/path',
        owner=user,
    )


# ── Base62 unit tests ─────────────────────────────────────────────────────────

def test_encode_base62_zero():
    assert encode_base62(0) == '0'


def test_encode_decode_roundtrip():
    for n in [1, 62, 999, 123456, 9999999]:
        assert decode_base62(encode_base62(n)) == n


def test_short_code_min_length():
    code = encode_base62(1)
    padded = '0' * (6 - len(code)) + code
    assert len(padded) >= 6


# ── ShortCodeService ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_generate_returns_string():
    code = ShortCodeService.generate()
    assert isinstance(code, str)
    assert len(code) >= 6


@pytest.mark.django_db
def test_validate_custom_alias_reserved():
    with pytest.raises(ValueError, match="reserved"):
        ShortCodeService.validate_custom_alias("admin")


@pytest.mark.django_db
def test_validate_custom_alias_too_short():
    with pytest.raises(ValueError):
        ShortCodeService.validate_custom_alias("ab")


@pytest.mark.django_db
def test_validate_custom_alias_taken(link):
    with pytest.raises(ValueError, match="already taken"):
        ShortCodeService.validate_custom_alias(link.short_code)


# ── LinkService ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_create_link_auto_code(user):
    link = LinkService.create_link('https://google.com', owner=user)
    assert link.short_code
    assert link.owner == user
    assert link.status == Link.Status.ACTIVE


@pytest.mark.django_db
def test_create_link_custom_alias(user):
    link = LinkService.create_link('https://google.com', owner=user, custom_alias='my-link')
    assert link.short_code == 'my-link'
    assert link.custom_alias is True


@pytest.mark.django_db
def test_create_link_duplicate_alias(user, link):
    with pytest.raises(ValueError):
        LinkService.create_link(
            'https://other.com',
            owner=user,
            custom_alias=link.short_code,
        )


@pytest.mark.django_db
def test_increment_click(link):
    LinkService.increment_click(link)
    link.refresh_from_db()
    assert link.click_count == 1


# ── Anonymous shortening ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_anonymous_shorten(client):
    res = client.post('/api/links/shorten/', {
        'original_url': 'https://github.com/openai',
    })
    assert res.status_code == 201
    assert 'short_code' in res.data
    assert res.data['short_code']


# ── Authenticated: create, list, detail ──────────────────────────────────────

@pytest.mark.django_db
def test_create_link_authenticated(auth_client):
    res = auth_client.post('/api/links/', {
        'original_url': 'https://anthropic.com',
    })
    assert res.status_code == 201
    assert 'short_url' in res.data


@pytest.mark.django_db
def test_create_link_with_custom_alias(auth_client):
    res = auth_client.post('/api/links/', {
        'original_url': 'https://anthropic.com',
        'custom_alias': 'anthropic',
    })
    assert res.status_code == 201
    assert res.data['short_code'] == 'anthropic'


@pytest.mark.django_db
def test_list_links(auth_client, link):
    res = auth_client.get('/api/links/')
    assert res.status_code == 200
    assert len(res.data) >= 1


@pytest.mark.django_db
def test_get_link_detail(auth_client, link):
    res = auth_client.get(f'/api/links/{link.short_code}/')
    assert res.status_code == 200
    assert res.data['short_code'] == link.short_code


@pytest.mark.django_db
def test_patch_link_status(auth_client, link):
    res = auth_client.patch(f'/api/links/{link.short_code}/', {
        'status': 'inactive',
    })
    assert res.status_code == 200
    assert res.data['status'] == 'inactive'


@pytest.mark.django_db
def test_delete_link(auth_client, link):
    res = auth_client.delete(f'/api/links/{link.short_code}/')
    assert res.status_code == 204
    assert not Link.objects.filter(pk=link.pk).exists()


# ── Redirect ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_redirect_active_link(client, link):
    res = client.get(f'/r/{link.short_code}/', follow=False)
    assert res.status_code == 302
    assert res['Location'] == link.original_url


@pytest.mark.django_db
def test_redirect_increments_click(client, link):
    client.get(f'/r/{link.short_code}/', follow=False)
    link.refresh_from_db()
    assert link.click_count == 1


@pytest.mark.django_db
def test_redirect_inactive_link(client, link):
    link.status = Link.Status.INACTIVE
    link.save()
    res = client.get(f'/r/{link.short_code}/', follow=False)
    assert res.status_code == 410


@pytest.mark.django_db
def test_redirect_not_found(client):
    res = client.get('/r/doesnotexist/', follow=False)
    assert res.status_code == 404


@pytest.mark.django_db
def test_owner_cannot_see_other_users_link(db, client):
    other = User.objects.create_user(email='other@example.com', password='pass12345')
    other_link = LinkService.create_link('https://example.com', owner=other)

    res = client.post('/api/auth/login/', {
        'email': 'other@example.com', 'password': 'pass12345'
    })
    # login as a third user
    third = User.objects.create_user(email='third@example.com', password='pass12345')
    res2 = client.post('/api/auth/login/', {
        'email': 'third@example.com', 'password': 'pass12345'
    })
    token = res2.data['tokens']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    res3 = client.get(f'/api/links/{other_link.short_code}/')
    assert res3.status_code == 404   # not 403 — don't reveal existence