# analytics/tasks.py
# Async tasks for analytics recording.
#
# record_click_task replaces the synchronous AnalyticsService.record_click()
# call in the redirect view. The redirect now returns in ~2ms instead of
# waiting for a DB write.
#
# bind=True gives the task access to self (for retries).
# max_retries=3 means transient DB/Redis failures don't lose click data.

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def record_click_task(
    self,
    link_id: str,
    ip_address: str = None,
    user_agent: str = '',
    referrer: str = '',
):
    """
    Records a single click event asynchronously.

    Called by the redirect view after returning the 302.
    Receives only serializable primitives — no Django model instances,
    no request objects. Celery serializes args to JSON.

    Retry behavior:
        - Retries up to 3 times on any exception
        - 5 second delay between retries
        - After 3 failures, the task moves to the dead-letter state
          (visible in Flower / Celery inspect)
    """
    from analytics.models import ClickEvent
    from analytics.parsers import parse_device_type
    from links.models import Link

    try:
        link = Link.objects.get(id=link_id)
    except Link.DoesNotExist:
        # Link was deleted between redirect and task execution — harmless
        logger.warning(f"record_click_task: link {link_id} not found, skipping.")
        return

    device_type = parse_device_type(user_agent)

    try:
        ClickEvent.objects.create(
            link=link,
            ip_address=ip_address or None,
            user_agent=user_agent,
            referrer=referrer[:2000],
            device_type=device_type,
        )
        logger.info(f"Click recorded async: {link.short_code} | device={device_type}")

    except Exception as exc:
        logger.error(f"record_click_task failed for link {link_id}: {exc}")
        raise self.retry(exc=exc)