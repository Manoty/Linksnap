# links/serializers.py
# Input validation and output shaping for link endpoints.

from rest_framework import serializers
from links.models import Link


class LinkCreateSerializer(serializers.Serializer):
    original_url  = serializers.URLField()
    custom_alias  = serializers.CharField(required=False, allow_blank=True, max_length=50)
    expires_at    = serializers.DateTimeField(required=False, allow_null=True)

    def validate_original_url(self, value):
        # Prevent shortening our own short links (redirect loops)
        if 'qejani.io' in value:
            raise serializers.ValidationError("You cannot shorten a Qejani link.")
        return value

    def validate_expires_at(self, value):
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value


class LinkSerializer(serializers.ModelSerializer):
    """
    Full link representation returned to the owner.
    short_url is a computed field — not stored in DB.
    """
    short_url  = serializers.SerializerMethodField()
    is_usable  = serializers.SerializerMethodField()

    class Meta:
        model  = Link
        fields = [
            'id', 'original_url', 'short_code', 'short_url',
            'custom_alias', 'status', 'is_usable',
            'click_count', 'expires_at', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_short_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/r/{obj.short_code}/')
        return f'/r/{obj.short_code}/'

    def get_is_usable(self, obj):
        return obj.is_usable


class LinkUpdateSerializer(serializers.Serializer):
    status     = serializers.ChoiceField(choices=Link.Status.choices, required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_expires_at(self, value):
        from django.utils import timezone
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value