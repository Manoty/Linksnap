# links/tests_tasks.py
# Tests for link lifecycle tasks.

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from links.models import Link
from links.services import LinkService
from links.tasks import expire_links_task, cleanup_anonymous_links_task

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='taskuser2@example.com',
        password='strongpass99',
    )


@pytest.mark.django_db
def test_expire_links_task(user, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    # Create a link that expired yesterday
    past = timezone.now() - timedelta(hours=1)
    link = LinkService.create_link(
        original_url='https://example.com',
        owner=user,
        expires_at=past,
    )

    result = expire_links_task.delay()

    link.refresh_from_db()
    assert link.status == Link.Status.EXPIRED


@pytest.mark.django_db
def test_expire_links_task_ignores_future(user, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    future = timezone.now() + timedelta(days=1)
    link = LinkService.create_link(
        original_url='https://example.com',
        owner=user,
        expires_at=future,
    )

    expire_links_task.delay()

    link.refresh_from_db()
    assert link.status == Link.Status.ACTIVE


@pytest.mark.django_db
def test_expire_links_returns_count(user, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    past = timezone.now() - timedelta(hours=1)
    LinkService.create_link('https://a.com', owner=user, expires_at=past)
    LinkService.create_link('https://b.com', owner=user, expires_at=past)

    result = expire_links_task.delay()
    assert result.get()['expired'] == 2


@pytest.mark.django_db
def test_cleanup_anonymous_links(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    # Create an old anonymous link
    link = LinkService.create_link('https://example.com', owner=None)
    Link.objects.filter(pk=link.pk).update(
        created_at=timezone.now() - timedelta(days=31)
    )

    result = cleanup_anonymous_links_task.delay()
    assert result.get()['deleted'] == 1
    assert not Link.objects.filter(pk=link.pk).exists()


@pytest.mark.django_db
def test_cleanup_keeps_recent_anonymous(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    # Recent anonymous link — should NOT be deleted
    link = LinkService.create_link('https://example.com', owner=None)

    cleanup_anonymous_links_task.delay()
    assert Link.objects.filter(pk=link.pk).exists()