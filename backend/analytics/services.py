# analytics/services.py
# All analytics business logic and aggregation queries.
# Views never touch ClickEvent directly — always go through this service.

import logging
from datetime import timedelta
from django.db.models import Count, Q
from django.utils import timezone

from analytics.models import ClickEvent
from analytics.parsers import extract_ip, parse_device_type

logger = logging.getLogger(__name__)


class AnalyticsService:

    @staticmethod
    def record_click(link, request=None) -> ClickEvent:
        """
        Creates a ClickEvent for a redirect hit.
        Designed to be called from the redirect view — sync for now,
        drops into Celery in Phase 5 with zero changes to the call site.

        If request is None (e.g. called from tests/scripts), we store
        a minimal event with no metadata.
        """
        ip         = extract_ip(request) if request else None
        user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
        referrer   = request.META.get('HTTP_REFERER', '') if request else ''
        device     = parse_device_type(user_agent)

        event = ClickEvent.objects.create(
            link=link,
            ip_address=ip,
            user_agent=user_agent,
            referrer=referrer[:2000],  # guard against malformed headers
            device_type=device,
        )

        logger.info(f"Click recorded: {link.short_code} | device={device}")
        return event

    # ── Per-link stats ────────────────────────────────────────────────────────

    @staticmethod
    def get_link_stats(link) -> dict:
        """
        Full stats for a single link.
        Returns click totals, device breakdown, referrer breakdown,
        and a 30-day daily time series.
        """
        qs = ClickEvent.objects.filter(link=link)

        total = qs.count()

        # Device breakdown
        device_breakdown = (
            qs.exclude(device_type='')
              .values('device_type')
              .annotate(count=Count('id'))
              .order_by('-count')
        )

        # Top referrers (non-empty, top 10)
        referrer_breakdown = (
            qs.exclude(referrer='')
              .values('referrer')
              .annotate(count=Count('id'))
              .order_by('-count')[:10]
        )

        # Daily clicks — last 30 days
        since = timezone.now() - timedelta(days=30)
        daily_clicks = (
            qs.filter(clicked_at__gte=since)
              .extra(select={'day': "DATE(clicked_at)"})
              .values('day')
              .annotate(count=Count('id'))
              .order_by('day')
        )

        # Last 10 clicks
        recent_clicks = qs.values(
            'clicked_at', 'device_type', 'referrer', 'country_code'
        )[:10]

        return {
            'link_id':          str(link.id),
            'short_code':       link.short_code,
            'total_clicks':     total,
            'device_breakdown': list(device_breakdown),
            'top_referrers':    list(referrer_breakdown),
            'daily_clicks':     list(daily_clicks),
            'recent_clicks':    list(recent_clicks),
        }

    # ── Dashboard-level stats (across all user links) ─────────────────────────

    @staticmethod
    def get_dashboard_stats(user) -> dict:
        """
        Aggregated stats across all links owned by a user.
        Powers the authenticated dashboard view.
        """
        from links.models import Link

        user_links = Link.objects.filter(owner=user)
        link_ids   = user_links.values_list('id', flat=True)

        total_links  = user_links.count()
        active_links = user_links.filter(status='active').count()

        total_clicks = ClickEvent.objects.filter(link_id__in=link_ids).count()

        # Top performing links — by click count (cached field, fast)
        top_links = (
            user_links
            .filter(click_count__gt=0)
            .order_by('-click_count')[:5]
        )

        # Clicks in the last 7 days
        since_7d = timezone.now() - timedelta(days=7)
        recent_clicks = ClickEvent.objects.filter(
            link_id__in=link_ids,
            clicked_at__gte=since_7d,
        ).count()

        # Daily trend — last 14 days
        since_14d = timezone.now() - timedelta(days=14)
        daily_trend = (
            ClickEvent.objects
            .filter(link_id__in=link_ids, clicked_at__gte=since_14d)
            .extra(select={'day': "DATE(clicked_at)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Device split across all links
        device_split = (
            ClickEvent.objects
            .filter(link_id__in=link_ids)
            .exclude(device_type='')
            .values('device_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        from links.serializers import LinkSerializer
        return {
            'total_links':   total_links,
            'active_links':  active_links,
            'total_clicks':  total_clicks,
            'clicks_7d':     recent_clicks,
            'top_links':     LinkSerializer(top_links, many=True).data,
            'daily_trend':   list(daily_trend),
            'device_split':  list(device_split),
        }

    @staticmethod
    def get_recent_activity(user, limit: int = 20) -> list:
        """
        Returns the most recent click events across all of a user's links.
        Used for the activity feed on the dashboard.
        """
        from links.models import Link

        link_ids = Link.objects.filter(owner=user).values_list('id', flat=True)

        events = (
            ClickEvent.objects
            .filter(link_id__in=link_ids)
            .select_related('link')
            .values(
                'clicked_at',
                'device_type',
                'referrer',
                'country_code',
                'link__short_code',
                'link__original_url',
            )
            .order_by('-clicked_at')[:limit]
        )

        return list(events)