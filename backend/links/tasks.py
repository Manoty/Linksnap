# links/tasks.py
# Periodic background tasks for link lifecycle management.

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def expire_links_task():
    """
    Bulk-marks all overdue active links as expired.
    Runs every 5 minutes via Celery Beat (configured in settings).

    Uses LinkService.mark_expired_links() so the business logic
    stays in one place and is independently testable.
    """
    from links.services import LinkService

    count = LinkService.mark_expired_links()
    logger.info(f"expire_links_task: marked {count} link(s) as expired.")
    return {'expired': count}


@shared_task
def cleanup_anonymous_links_task():
    """
    Deletes anonymous links (owner=None) older than 30 days.
    Keeps the links table lean. Runs daily via Beat — add to
    CELERY_BEAT_SCHEDULE in settings when you're ready.
    """
    from django.utils import timezone
    from datetime import timedelta
    from links.models import Link

    cutoff  = timezone.now() - timedelta(days=30)
    deleted, _ = Link.objects.filter(
        owner__isnull=True,
        created_at__lt=cutoff,
    ).delete()

    logger.info(f"cleanup_anonymous_links_task: deleted {deleted} stale anonymous links.")
    return {'deleted': deleted}