# links/services.py
# All link business logic. Views call this. Never the other way.
# Transactions wrap writes so we never have partial state in the DB.

import logging
from django.db import transaction
from django.utils import timezone

from links.models import Link
from links.short_code import ShortCodeService

logger = logging.getLogger(__name__)


class LinkService:

    @staticmethod
    @transaction.atomic
    def create_link(
        original_url: str,
        owner=None,
        custom_alias: str = None,
        expires_at=None,
    ) -> Link:
        """
        Creates a shortened link.

        - Authenticated users can pass a custom_alias and expires_at.
        - Anonymous users get an auto-generated code, no expiry control.
        - Wrapped in a transaction so code generation + insert are atomic.
        """
        if custom_alias:
            short_code = ShortCodeService.validate_custom_alias(custom_alias)
            is_custom  = True
        else:
            short_code = ShortCodeService.generate()
            is_custom  = False

        link = Link.objects.create(
            original_url=original_url,
            short_code=short_code,
            custom_alias=is_custom,
            owner=owner,
            expires_at=expires_at,
        )

        logger.info(f"Link created: {short_code} → {original_url[:80]} (owner={owner})")
        return link

    @staticmethod
    def get_link_by_code(short_code: str) -> Link | None:
        """
        Fetches a link by short code. Returns None if not found.
        Hot path — short_code is indexed.
        """
        try:
            return Link.objects.get(short_code=short_code)
        except Link.DoesNotExist:
            return None

    @staticmethod
    def get_user_links(user, status_filter: str = None):
        """
        Returns all links for a given user.
        Optionally filtered by status.
        """
        qs = Link.objects.filter(owner=user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @staticmethod
    @transaction.atomic
    def increment_click(link: Link) -> None:
        """
        Atomically increments the click counter.
        Uses select_for_update() to prevent race conditions under
        concurrent redirect traffic. Phase 4 moves this to Celery.
        """
        Link.objects.select_for_update().filter(pk=link.pk).update(
            click_count=link.click_count + 1
        )

    @staticmethod
    @transaction.atomic
    def deactivate_link(link: Link, user) -> Link:
        """
        Deactivates a link. Only the owner can do this.
        """
        if link.owner != user:
            raise PermissionError("You do not have permission to modify this link.")
        link.status = Link.Status.INACTIVE
        link.save(update_fields=['status', 'updated_at'])
        return link

    @staticmethod
    @transaction.atomic
    def delete_link(link: Link, user) -> None:
        """
        Hard deletes a link. Only the owner can do this.
        """
        if link.owner != user:
            raise PermissionError("You do not have permission to delete this link.")
        link.delete()

    @staticmethod
    def mark_expired_links() -> int:
        """
        Bulk-marks overdue links as expired.
        Called by a Celery task in Phase 5.
        Returns count of links updated.
        """
        now = timezone.now()
        updated = Link.objects.filter(
            status=Link.Status.ACTIVE,
            expires_at__lte=now,
        ).update(status=Link.Status.EXPIRED)

        if updated:
            logger.info(f"Marked {updated} link(s) as expired.")
        return updated