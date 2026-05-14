# analytics/views.py
# Analytics endpoints. All read-only. All require authentication.
# Thin views — AnalyticsService does all the work.

import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services import AnalyticsService
from links.services import LinkService

logger = logging.getLogger(__name__)


class DashboardStatsView(APIView):
    """
    GET /api/analytics/dashboard/
    Aggregated stats across all links for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = AnalyticsService.get_dashboard_stats(request.user)
        return Response(stats)


class LinkStatsView(APIView):
    """
    GET /api/analytics/links/{short_code}/
    Per-link click analytics. Only the owner can access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, short_code: str):
        link = LinkService.get_link_by_code(short_code)

        if link is None:
            return Response({'detail': 'Link not found.'}, status=404)

        if link.owner != request.user:
            return Response({'detail': 'Not found.'}, status=404)

        stats = AnalyticsService.get_link_stats(link)
        return Response(stats)


class RecentActivityView(APIView):
    """
    GET /api/analytics/activity/
    Last N click events across all user links.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit  = min(int(request.query_params.get('limit', 20)), 100)
        events = AnalyticsService.get_recent_activity(request.user, limit=limit)
        return Response({'results': events, 'count': len(events)})