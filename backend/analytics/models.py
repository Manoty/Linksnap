# analytics/models.py
# ClickEvent stores one record per redirect hit.
# This is the raw event log — never aggregate in-place, always query.
#
# Design notes:
#   - No FK to User intentionally. A click belongs to a Link, not a user.
#     The owner relationship is Link → User. Don't duplicate it here.
#   - ip_address is nullable — we'll anonymize it for GDPR in a later phase.
#   - user_agent / referrer are raw strings. Parsing happens in the service
#     layer, not at storage time, so we never lose the original data.

import uuid
from django.db import models


class ClickEvent(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link       = models.ForeignKey(
                     'links.Link',
                     on_delete=models.CASCADE,
                     related_name='click_events',
                 )

    # Request metadata — all nullable, we can't always get them
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    referrer   = models.URLField(max_length=2000, blank=True, default='')

    # Parsed fields — populated by service layer, not raw request
    # Phase 5 adds: country, city, device_type, browser, os
    country_code = models.CharField(max_length=2, blank=True, default='')
    device_type  = models.CharField(max_length=20, blank=True, default='')
    # e.g. 'mobile', 'desktop', 'tablet', 'bot'

    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'analytics_clickevent'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['link', '-clicked_at']),
            models.Index(fields=['clicked_at']),
            models.Index(fields=['link', 'device_type']),
        ]

    def __str__(self):
        return f"Click on {self.link.short_code} at {self.clicked_at}"