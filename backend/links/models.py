# Core Link model. Every shortened URL is a Link record.
# UUID PK — no sequential ID leakage via the API.
# short_code is indexed — it's the hottest read path in the whole system.

import uuid
from django.conf import settings
from django.db import models


class Link(models.Model):

    class Status(models.TextChoices):
        ACTIVE   = 'active',   'Active'
        INACTIVE = 'inactive', 'Inactive'
        EXPIRED  = 'expired',  'Expired'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner      = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     on_delete=models.CASCADE,
                     null=True,
                     blank=True,
                     related_name='links',
                 )

    original_url = models.TextField()
    short_code   = models.CharField(max_length=20, unique=True, db_index=True)
    custom_alias = models.BooleanField(default=False)  # was this user-supplied?

    status       = models.CharField(
                       max_length=10,
                       choices=Status.choices,
                       default=Status.ACTIVE,
                   )

    expires_at   = models.DateTimeField(null=True, blank=True)

    click_count  = models.PositiveIntegerField(default=0)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'links_link'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.short_code} → {self.original_url[:60]}"

    @property
    def is_usable(self) -> bool:
        """
        Single method to check if a link can be redirected.
        Redirect endpoint calls this — nothing else needs to know the rules.
        """
        from django.utils import timezone

        if self.status != self.Status.ACTIVE:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True