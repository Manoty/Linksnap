# Health check view. Used by Docker, load balancers, and uptime monitors.
# Thin view — no business logic here.

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("Health check called")
        return Response({
            "status": "ok",
            "service": "qejani-api",
            "version": "1.0.0"
        })