# Tests for async click recording task.
# Tasks are tested synchronously (CELERY_TASK_ALWAYS_EAGER)
# so we don't need a running broker in CI.

import pytest
from django.contrib.auth import get_user_model
from analytics.models import ClickEvent
from analytics.tasks import record_click_task
from links.services import LinkService

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='taskuser@example.com',
        password='strongpass99',
    )


@pytest.fixture
def link(db, user):
    return LinkService.create_link(
        original_url='https://example.com',
        owner=user,
    )


@pytest.mark.django_db
def test_record_click_task_creates_event(link, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    record_click_task.delay(
        link_id=str(link.id),
        ip_address='127.0.0.1',
        user_agent='Mozilla/5.0 (Windows NT 10.0)',
        referrer='https://google.com',
    )

    assert ClickEvent.objects.filter(link=link).count() == 1
    event = ClickEvent.objects.get(link=link)
    assert event.device_type == 'desktop'
    assert event.referrer == 'https://google.com'


@pytest.mark.django_db
def test_record_click_task_missing_link(settings):
    """Task should not crash when link is deleted mid-flight."""
    settings.CELERY_TASK_ALWAYS_EAGER = True

    # No exception should be raised
    record_click_task.delay(
        link_id='00000000-0000-0000-0000-000000000000',
        ip_address='127.0.0.1',
    )

    assert ClickEvent.objects.count() == 0


@pytest.mark.django_db
def test_record_click_task_mobile_device(link, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    record_click_task.delay(
        link_id=str(link.id),
        ip_address='1.2.3.4',
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)',
        referrer='',
    )

    event = ClickEvent.objects.get(link=link)
    assert event.device_type == 'mobile'