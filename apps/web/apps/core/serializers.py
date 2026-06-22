from rest_framework import serializers

from apps.users.models import User


class BaseSerializer(serializers.Serializer):
    """Base serializer for non-model (input/action) use cases."""

    def get_missing_fields(self, attrs, required_fields):
        missing = []
        for f in required_fields:
            val = attrs.get(f)
            if val is None or val == "":
                missing.append(f)
        return missing

    def validate_required_fields(self, attrs, required_fields):
        missing = self.get_missing_fields(attrs, required_fields)
        if missing:
            raise serializers.ValidationError({"missing_fields": missing})


class BaseModelSerializer(serializers.ModelSerializer):
    """Base serializer for model-bound use cases."""

    class Meta:
        pass


class UserMiniSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    profile_code = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    def get_id(self, obj):
        try:
            return obj.profile.code
        except Exception:
            return None

    def get_profile_code(self, obj):
        try:
            return obj.profile.code
        except Exception:
            return None

    def get_display_name(self, obj):
        try:
            return obj.profile.display_name or ""
        except Exception:
            return ""

    class Meta:
        model = User
        fields = ["id", "profile_code", "email", "display_name"]


class CodeSerializer(serializers.ModelSerializer):
    """Base Serializer with code"""

    code = serializers.CharField(read_only=True)

    class Meta:
        pass


class TimeStampedSerializer(serializers.ModelSerializer):
    """Base Serializer with created_at and updated_at"""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        pass


class AuditableSerializer(serializers.ModelSerializer):
    """Base Serializer with created_at, created_by, updated_at, and updated_by"""

    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta:
        pass


class ReadMixin:
    """For detail read projections."""

    pass


class ListMixin:
    """For list read projections."""

    pass


class WriteMixin:
    """For write/update-like."""

    pass


class ExportMixin:
    """For export read projections."""

    pass


class ImportMixin:
    """For import/write-like."""

    pass


class DynamicFieldsMixin:
    """
    For dynamic use-cases which are separate from read/list/export/import/write/update.
    """

    pass
