from rest_framework import serializers

from apps.core.serializers import BaseSerializer, ReadMixin


class MetaUserSerializer(ReadMixin, BaseSerializer):
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)


class MetaSerializer(ReadMixin, BaseSerializer):
    setup_complete = serializers.BooleanField(read_only=True)
    app_name = serializers.CharField(read_only=True)
    auth_mode = serializers.CharField(read_only=True)
    allow_registration = serializers.BooleanField(read_only=True)
    user = MetaUserSerializer(read_only=True, required=False)
