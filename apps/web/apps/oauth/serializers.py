from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    BaseSerializer,
    CodeSerializer,
    ReadMixin,
    WriteMixin,
)
from apps.oauth.models import OAuth


class OAuthSerializer(ReadMixin, AuditableSerializer, CodeSerializer):
    name = serializers.CharField(read_only=True)
    client_id = serializers.CharField(read_only=True)
    auth_endpoint = serializers.URLField(read_only=True)
    token_endpoint = serializers.URLField(read_only=True)
    userinfo_endpoint = serializers.URLField(read_only=True)
    scope = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = OAuth
        fields = [
            "code",
            "name",
            "client_id",
            "auth_endpoint",
            "token_endpoint",
            "userinfo_endpoint",
            "scope",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class OAuthCreateSerializer(WriteMixin, BaseSerializer):
    name = serializers.CharField(required=True)
    client_id = serializers.CharField(required=True)
    client_secret = serializers.CharField(required=True, write_only=True)
    auth_endpoint = serializers.CharField(required=True)
    token_endpoint = serializers.CharField(required=True)
    userinfo_endpoint = serializers.CharField(required=True)
    scope = serializers.CharField(required=True)
