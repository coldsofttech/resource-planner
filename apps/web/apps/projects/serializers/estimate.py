from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectEstimate, ProjectEstimateStatusHistory


class _UserMiniInlineSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_id(self, obj):
        try:
            return obj.profile.code
        except Exception:
            return None

    def get_name(self, obj) -> str:
        parts = [obj.first_name, obj.last_name]
        return " ".join(p for p in parts if p) or obj.email

    class Meta:
        from apps.users.models import User

        model = User
        fields = ["id", "email", "name"]


class ProjectEstimateListSerializer(ListMixin, CodeSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    version = serializers.IntegerField(read_only=True)
    version_display = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    estimate_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    contingency_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    day_rate = serializers.IntegerField(read_only=True)
    total_cost = serializers.FloatField(read_only=True)
    size = serializers.CharField(read_only=True)
    estimate_link = serializers.URLField(read_only=True, allow_blank=True)
    approval_email_sent = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectEstimate
        fields = [
            "code",
            "project_code",
            "project_name",
            "version",
            "version_display",
            "status",
            "estimate_days",
            "contingency_percentage",
            "day_rate",
            "total_cost",
            "size",
            "estimate_link",
            "approval_email_sent",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectEstimateDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    project_code = serializers.CharField(source="project.code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    version = serializers.IntegerField(read_only=True)
    version_display = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    estimate_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    contingency_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    day_rate = serializers.IntegerField(read_only=True)
    total_cost = serializers.FloatField(read_only=True)
    size = serializers.CharField(read_only=True)
    estimate_link = serializers.URLField(read_only=True, allow_blank=True)
    shared_by = _UserMiniInlineSerializer(many=True, read_only=True)
    reviewed_by = _UserMiniInlineSerializer(many=True, read_only=True)
    approval_email_sent = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectEstimate
        fields = [
            "code",
            "project_code",
            "project_name",
            "version",
            "version_display",
            "status",
            "estimate_days",
            "contingency_percentage",
            "day_rate",
            "total_cost",
            "size",
            "estimate_link",
            "shared_by",
            "reviewed_by",
            "approval_email_sent",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectEstimateCreateSerializer(WriteMixin, serializers.Serializer):
    estimate_link = serializers.URLField(required=False, allow_blank=True, default="")
    shared_by_codes = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1,
        error_messages={
            "required": "At least one person must be specified in Shared By."
        },
    )
    reviewed_by_codes = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    status = serializers.ChoiceField(
        choices=ProjectEstimate._meta.get_field("status").choices,
        required=False,
        default="DRAFT",
    )
    estimate_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=0
    )
    contingency_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=0
    )
    day_rate = serializers.IntegerField(required=False, allow_null=True, default=None)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class ProjectEstimateUpdateSerializer(WriteMixin, serializers.Serializer):
    estimate_link = serializers.URLField(required=False, allow_blank=True)
    shared_by_codes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    reviewed_by_codes = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    status = serializers.ChoiceField(
        choices=ProjectEstimate._meta.get_field("status").choices,
        required=False,
    )
    estimate_days = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    contingency_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )
    day_rate = serializers.IntegerField(required=False)
    approval_email_sent = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ProjectEstimateStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ProjectEstimateStatusHistory
        fields = [
            "id",
            "action",
            "previous_status",
            "new_status",
            "note",
            "changed_on",
            "changed_by",
        ]
