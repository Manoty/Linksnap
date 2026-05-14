# analytics/tests.py
# Tests for: click recording, device parsing, per-link stats,
# dashboard stats, activity feed, and access control.

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from analytics.models import ClickEvent
from analytics.parsers import parse_device_type, extract_ip
from analytics.services import AnalyticsService
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
def other_user(db):
    return User.objects.create_user(
        email='other@example.com',
        password='strongpass99',
    )


@pytest.fixture
def auth_client(client, user):
    res = client.post('/api/auth/login/', {
        'email': 'owner@example.com',
        'password': 'strongpass99',
    })
    client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {res.data["tokens"]["access"]}'
    )
    return client


@pytest.fixture
def link(db, user):
    return LinkService.create_link(
        original_url='https://example.com/page',
        owner=user,
    )


@pytest.fixture
def link_with_clicks(db, link):
    """A link pre-loaded with 5 click events."""
    for _ in range(5):
        AnalyticsService.record_click(link, request=None)
    link.click_count = 5
    link.save(update_fields=['click_count'])
    return link


# ── Parser unit tests ─────────────────────────────────────────────────────────

def test_parse_device_mobile():
    ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
    assert parse_device_type(ua) == 'mobile'


def test_parse_device_tablet():
    ua = 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)'
    assert parse_device_type(ua) == 'tablet'


def test_parse_device_bot():
    ua = 'Googlebot/2.1 (+http://www.google.com/bot.html)'
    assert parse_device_type(ua) == 'bot'


def test_parse_device_desktop():
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    assert parse_device_type(ua) == 'desktop'


def test_parse_device_empty():
    assert parse_device_type('') == ''


# ── ClickEvent recording ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_record_click_no_request(link):
    event = AnalyticsService.record_click(link, request=None)
    assert event.pk is not None
    assert event.link == link
    assert event.ip_address is None
    assert event.device_type == ''


@pytest.mark.django_db
def test_record_click_creates_event(link):
    AnalyticsService.record_click(link, request=None)
    assert ClickEvent.objects.filter(link=link).count() == 1


@pytest.mark.django_db
def test_record_multiple_clicks(link):
    for _ in range(7):
        AnalyticsService.record_click(link, request=None)
    assert ClickEvent.objects.filter(link=link).count() == 7


# ── Per-link stats ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_get_link_stats_structure(link_with_clicks):
    stats = AnalyticsService.get_link_stats(link_with_clicks)

    assert stats['total_clicks'] == 5
    assert stats['short_code'] == link_with_clicks.short_code
    assert 'device_breakdown' in stats
    assert 'top_referrers' in stats
    assert 'daily_clicks' in stats
    assert 'recent_clicks' in stats


@pytest.mark.django_db
def test_get_link_stats_zero_clicks(link):
    stats = AnalyticsService.get_link_stats(link)
    assert stats['total_clicks'] == 0
    assert stats['daily_clicks'] == []


# ── Dashboard stats ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dashboard_stats_structure(user, link_with_clicks):
    stats = AnalyticsService.get_dashboard_stats(user)

    assert 'total_links' in stats
    assert 'active_links' in stats
    assert 'total_clicks' in stats
    assert 'clicks_7d' in stats
    assert 'top_links' in stats
    assert 'daily_trend' in stats
    assert 'device_split' in stats


@pytest.mark.django_db
def test_dashboard_stats_counts(user, link_with_clicks):
    stats = AnalyticsService.get_dashboard_stats(user)
    assert stats['total_links'] == 1
    assert stats['active_links'] == 1
    assert stats['total_clicks'] == 5


@pytest.mark.django_db
def test_dashboard_stats_empty_user(user):
    stats = AnalyticsService.get_dashboard_stats(user)
    assert stats['total_links'] == 0
    assert stats['total_clicks'] == 0


# ── Recent activity ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_recent_activity_returns_events(user, link_with_clicks):
    activity = AnalyticsService.get_recent_activity(user)
    assert len(activity) == 5


@pytest.mark.django_db
def test_recent_activity_limit(user, link_with_clicks):
    activity = AnalyticsService.get_recent_activity(user, limit=3)
    assert len(activity) == 3


@pytest.mark.django_db
def test_recent_activity_empty(user):
    activity = AnalyticsService.get_recent_activity(user)
    assert activity == []


# ── API endpoints ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dashboard_endpoint(auth_client, link_with_clicks):
    res = auth_client.get('/api/analytics/dashboard/')
    assert res.status_code == 200
    assert 'total_clicks' in res.data
    assert res.data['total_clicks'] == 5


@pytest.mark.django_db
def test_link_stats_endpoint(auth_client, link_with_clicks):
    res = auth_client.get(f'/api/analytics/links/{link_with_clicks.short_code}/')
    assert res.status_code == 200
    assert res.data['total_clicks'] == 5


@pytest.mark.django_db
def test_link_stats_wrong_owner(client, other_user, link):
    res = client.post('/api/auth/login/', {
        'email': 'other@example.com',
        'password': 'strongpass99',
    })
    token = res.data['tokens']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    res = client.get(f'/api/analytics/links/{link.short_code}/')
    assert res.status_code == 404


@pytest.mark.django_db
def test_activity_endpoint(auth_client, link_with_clicks):
    res = auth_client.get('/api/analytics/activity/')
    assert res.status_code == 200
    assert res.data['count'] == 5


@pytest.mark.django_db
def test_activity_endpoint_limit(auth_client, link_with_clicks):
    res = auth_client.get('/api/analytics/activity/?limit=2')
    assert res.status_code == 200
    assert res.data['count'] == 2


@pytest.mark.django_db
def test_analytics_requires_auth(client):
    res = client.get('/api/analytics/dashboard/')
    assert res.status_code == 401


# ── Redirect records click end-to-end ─────────────────────────────────────────

@pytest.mark.django_db
def test_redirect_records_click_event(client, link):
    assert ClickEvent.objects.filter(link=link).count() == 0
    client.get(f'/r/{link.short_code}/', follow=False)
    assert ClickEvent.objects.filter(link=link).count() == 1


@pytest.mark.django_db
def test_redirect_click_event_has_correct_link(client, link):
    client.get(f'/r/{link.short_code}/', follow=False)
    event = ClickEvent.objects.get(link=link)
    assert event.link.short_code == link.short_code