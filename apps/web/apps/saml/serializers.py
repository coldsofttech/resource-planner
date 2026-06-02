from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    BaseSerializer,
    CodeSerializer,
    ReadMixin,
    WriteMixin,
)
from apps.saml.models import SAML


class SAMLSerializer(ReadMixin, AuditableSerializer, CodeSerializer):
    name = serializers.CharField(read_only=True)
    idp_entity_id = serializers.URLField(read_only=True)
    idp_sso_url = serializers.URLField(read_only=True)
    idp_x509_cert = serializers.CharField(read_only=True)
    sp_entity_id = serializers.URLField(read_only=True)
    sp_assertion_url = serializers.URLField(read_only=True)
    icon = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = SAML
        fields = [
            "code",
            "name",
            "idp_entity_id",
            "idp_sso_url",
            "idp_x509_cert",
            "sp_entity_id",
            "sp_assertion_url",
            "icon",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class SAMLCreateSerializer(WriteMixin, BaseSerializer):
    name = serializers.CharField(required=True)
    idp_entity_id = serializers.URLField(required=True)
    idp_sso_url = serializers.URLField(required=True)
    idp_x509_cert = serializers.CharField(required=True)
    sp_entity_id = serializers.URLField(required=False, allow_blank=True)
    sp_assertion_url = serializers.URLField(required=True)
    icon = serializers.CharField(required=False, allow_blank=True, default="")
