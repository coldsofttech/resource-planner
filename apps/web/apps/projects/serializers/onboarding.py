from __future__ import annotations

from rest_framework import serializers

from apps.projects.models import (
    Onboarding,
    OnboardingAttachment,
    OnboardingContact,
    OnboardingLink,
)


class OnboardingContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingContact
        fields = ["code", "email", "name", "role"]


class OnboardingLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingLink
        fields = ["code", "url", "title"]


class OnboardingAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingAttachment
        fields = ["code", "file_name", "content_type", "file_size"]


class OnboardingListSerializer(serializers.ModelSerializer):
    requester = OnboardingContactSerializer(read_only=True)
    product_names = serializers.SerializerMethodField()
    business_unit_names = serializers.SerializerMethodField()

    class Meta:
        model = Onboarding
        fields = [
            "code",
            "project_name",
            "status",
            "requester",
            "product_names",
            "business_unit_names",
            "created_at",
        ]

    def get_product_names(self, obj: Onboarding) -> list[str]:
        return [p.name for p in obj.products.all()]

    def get_business_unit_names(self, obj: Onboarding) -> list[str]:
        return [bu.name for bu in obj.business_units.all()]


class OnboardingDetailSerializer(serializers.ModelSerializer):
    requester = OnboardingContactSerializer(read_only=True)
    accountable_executive = OnboardingContactSerializer(read_only=True)
    contacts = OnboardingContactSerializer(many=True, read_only=True)
    links = OnboardingLinkSerializer(many=True, read_only=True)
    attachments = OnboardingAttachmentSerializer(many=True, read_only=True)
    products = serializers.SerializerMethodField()
    business_unit_names = serializers.SerializerMethodField()
    project_code_ref = serializers.SerializerMethodField()
    project_name_ref = serializers.SerializerMethodField()

    class Meta:
        model = Onboarding
        fields = [
            "code",
            "project_name",
            "status",
            "requirements",
            "risk",
            "project_code",
            "tentative_start_date",
            "tentative_end_date",
            "requester",
            "accountable_executive",
            "contacts",
            "products",
            "business_unit_names",
            "links",
            "attachments",
            "project_code_ref",
            "project_name_ref",
            "created_at",
        ]

    def get_products(self, obj: Onboarding) -> list[dict]:
        return [{"code": p.code, "name": p.name} for p in obj.products.all()]

    def get_business_unit_names(self, obj: Onboarding) -> list[str]:
        return [bu.name for bu in obj.business_units.all()]

    def get_project_code_ref(self, obj: Onboarding) -> str | None:
        return obj.project.code if obj.project_id else None

    def get_project_name_ref(self, obj: Onboarding) -> str | None:
        return obj.project.name if obj.project_id else None


class _LinkInput(serializers.Serializer):
    url = serializers.URLField()
    title = serializers.CharField(
        max_length=200, required=False, allow_blank=True, default=""
    )


class OnboardingSubmitSerializer(serializers.Serializer):
    project_name = serializers.CharField(max_length=255)
    requester_email = serializers.EmailField()
    requirements = serializers.CharField(required=False, default="", allow_blank=True)
    risk = serializers.CharField(required=False, default="", allow_blank=True)
    project_code = serializers.CharField(
        max_length=50, required=False, default="", allow_blank=True
    )
    tentative_start_date = serializers.DateField(required=False, allow_null=True)
    tentative_end_date = serializers.DateField(required=False, allow_null=True)
    product_codes = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    business_unit_codes = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, default=list
    )
    accountable_executive_email = serializers.EmailField(
        required=False, allow_blank=True, default=""
    )
    contact_emails = serializers.ListField(
        child=serializers.EmailField(), required=False, default=list
    )
    links = _LinkInput(many=True, required=False, default=list)
