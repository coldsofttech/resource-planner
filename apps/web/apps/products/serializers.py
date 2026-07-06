from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.products.models import Product


class BusinessUnitMiniSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class ProductListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    business_unit = BusinessUnitMiniSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Product
        fields = [
            "code",
            "name",
            "short_name",
            "business_unit",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProductDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    business_unit = BusinessUnitMiniSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Product
        fields = [
            "code",
            "name",
            "short_name",
            "business_unit",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProductCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    short_name = serializers.CharField(max_length=10, required=True)
    business_unit_code = serializers.CharField(max_length=50, required=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProductUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    short_name = serializers.CharField(max_length=10, required=False)
    business_unit_code = serializers.CharField(max_length=50, required=False)
    is_active = serializers.BooleanField(required=False)
