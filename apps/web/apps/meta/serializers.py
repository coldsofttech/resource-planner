from rest_framework import serializers

from apps.core.serializers import BaseSerializer, ReadMixin


class MetaUserSerializer(ReadMixin, BaseSerializer):
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)


class MetaSSOProviderSerializer(ReadMixin, BaseSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)


class MetaSerializer(ReadMixin, BaseSerializer):
    setup_complete = serializers.BooleanField(read_only=True)
    app_name = serializers.CharField(read_only=True)
    auth_mode = serializers.CharField(read_only=True)
    allow_registration = serializers.BooleanField(read_only=True)
    oauth_provider = MetaSSOProviderSerializer(
        read_only=True, required=False, allow_null=True
    )
    saml_provider = MetaSSOProviderSerializer(
        read_only=True, required=False, allow_null=True
    )
    user = MetaUserSerializer(read_only=True, required=False)
