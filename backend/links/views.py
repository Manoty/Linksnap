# links/views.py
# Link management views (authenticated) + public redirect view.
# Views are deliberately thin. All logic is in LinkService.

import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from links.models import Link
from links.serializers import LinkCreateSerializer, LinkSerializer, LinkUpdateSerializer
from links.services import LinkService

logger = logging.getLogger(__name__)


# ── Public: Redirect ─────────────────────────────────────────────────────────

class RedirectView(APIView):
    """
    GET /r/{short_code}/
    The most performance-critical endpoint in the system.
    Looks up the link, validates usability, logs the click, redirects.
    """
    permission_classes = [AllowAny]

    def get(self, request, short_code: str):
        from django.http import HttpResponseRedirect

        link = LinkService.get_link_by_code(short_code)

        if link is None:
            return Response(
                {'detail': 'Link not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not link.is_usable:
            return Response(
                {'detail': 'This link is inactive or has expired.'},
                status=status.HTTP_410_GONE,
            )

        # Increment click count — moves to async Celery task in Phase 5
        LinkService.increment_click(link)

        return HttpResponseRedirect(link.original_url)


# ── Authenticated: Link Management ───────────────────────────────────────────

class LinkListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all links owned by the authenticated user."""
        status_filter = request.query_params.get('status')
        links = LinkService.get_user_links(request.user, status_filter=status_filter)
        serializer = LinkSerializer(links, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """Create a new shortened link."""
        serializer = LinkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            link = LinkService.create_link(
                original_url=serializer.validated_data['original_url'],
                owner=request.user,
                custom_alias=serializer.validated_data.get('custom_alias'),
                expires_at=serializer.validated_data.get('expires_at'),
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            LinkSerializer(link, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class LinkDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_owned_link(self, short_code: str, user):
        """
        Shared helper — fetches a link and verifies ownership.
        Returns (link, error_response). Caller checks error_response first.
        """
        link = LinkService.get_link_by_code(short_code)
        if link is None:
            return None, Response(
                {'detail': 'Link not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if link.owner != user:
            return None, Response(
                {'detail': 'Not found.'},    # don't reveal existence to non-owners
                status=status.HTTP_404_NOT_FOUND,
            )
        return link, None

    def get(self, request, short_code: str):
        link, err = self._get_owned_link(short_code, request.user)
        if err:
            return err
        return Response(LinkSerializer(link, context={'request': request}).data)

    def patch(self, request, short_code: str):
        link, err = self._get_owned_link(short_code, request.user)
        if err:
            return err

        serializer = LinkUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        if 'status' in data:
            link.status = data['status']
        if 'expires_at' in data:
            link.expires_at = data['expires_at']

        link.save(update_fields=['status', 'expires_at', 'updated_at'])
        return Response(LinkSerializer(link, context={'request': request}).data)

    def delete(self, request, short_code: str):
        link, err = self._get_owned_link(short_code, request.user)
        if err:
            return err

        try:
            LinkService.delete_link(link, request.user)
        except PermissionError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Anonymous shortening ──────────────────────────────────────────────────────

class AnonymousLinkCreateView(APIView):
    """
    POST /api/links/shorten/
    Anonymous users can shorten URLs. No auth, no custom alias, no expiry.
    Rate limited in Phase 5.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LinkCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            link = LinkService.create_link(
                original_url=serializer.validated_data['original_url'],
                owner=None,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            LinkSerializer(link, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )