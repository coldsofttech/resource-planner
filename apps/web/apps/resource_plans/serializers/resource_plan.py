from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.resource_plans.constants import PlanType
from apps.resource_plans.models import Plan


class ResourcePlanListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    plan_type = serializers.CharField(read_only=True)
    plan_type_display = serializers.SerializerMethodField()
    financial_year_code = serializers.SerializerMethodField()
    financial_year_display = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_head = serializers.BooleanField(read_only=True)
    latest_version_threshold = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_plan_type_display(self, obj) -> str:
        return obj.get_plan_type_display()

    def get_financial_year_code(self, obj) -> str | None:
        return obj.financial_year.code if obj.financial_year else None

    def get_financial_year_display(self, obj) -> str | None:
        return obj.financial_year.short_fy if obj.financial_year else None

    def get_latest_version_threshold(self, obj) -> float | None:
        versions = sorted(obj.versions.all(), key=lambda v: v.version, reverse=True)
        if not versions:
            return None
        return float(versions[0].threshold_percentage)

    class Meta(CodeSerializer.Meta):
        model = Plan
        fields = [
            "code",
            "name",
            "description",
            "plan_type",
            "plan_type_display",
            "financial_year_code",
            "financial_year_display",
            "is_active",
            "is_head",
            "latest_version_threshold",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ResourcePlanVersionSerializer(serializers.Serializer):
    version = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    threshold_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()


class ResourcePlanVersionDetailSerializer(serializers.Serializer):
    version = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    threshold_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    plan_code = serializers.SerializerMethodField()
    plan_name = serializers.SerializerMethodField()
    financial_year_code = serializers.SerializerMethodField()
    cloned_from_version = serializers.SerializerMethodField()
    sprint_point_price = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_status_display(self, obj) -> str:
        return obj.get_status_display()

    def get_plan_code(self, obj) -> str:
        return obj.plan.code

    def get_plan_name(self, obj) -> str:
        return obj.plan.name

    def get_financial_year_code(self, obj) -> str | None:
        return obj.plan.financial_year.code if obj.plan.financial_year_id else None

    def get_cloned_from_version(self, obj) -> int | None:
        return obj.cloned_from.version if obj.cloned_from_id else None

    def get_sprint_point_price(self, obj) -> int:
        from apps.configurations.selectors import Sprint as SprintConfig

        return SprintConfig.get_sprint_point_price()


class ResourcePlanVersionCreateSerializer(WriteMixin, serializers.Serializer):
    threshold_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=True, min_value=0, max_value=100
    )


class ResourcePlanVersionHistorySerializer(serializers.Serializer):
    action = serializers.CharField(read_only=True)
    action_display = serializers.SerializerMethodField()
    resource_code = serializers.CharField(read_only=True)
    before = serializers.JSONField(read_only=True)
    after = serializers.JSONField(read_only=True)
    actor = UserMiniSerializer(read_only=True, allow_null=True)
    timestamp = serializers.DateTimeField(read_only=True)

    def get_action_display(self, obj) -> str:
        return obj.get_action_display()


class ResourcePlanScopeSerializer(serializers.Serializer):
    financial_year_code = serializers.SerializerMethodField()
    financial_year_display = serializers.SerializerMethodField()
    programme_code = serializers.SerializerMethodField()
    programme_name = serializers.SerializerMethodField()
    project_code = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    team_code = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    def get_financial_year_code(self, obj) -> str | None:
        return obj.financial_year.code if obj.financial_year else None

    def get_financial_year_display(self, obj) -> str | None:
        return obj.financial_year.short_fy if obj.financial_year else None

    def get_programme_code(self, obj) -> str | None:
        return obj.programme.code if obj.programme else None

    def get_programme_name(self, obj) -> str | None:
        return obj.programme.name if obj.programme else None

    def get_project_code(self, obj) -> str | None:
        return obj.project.code if obj.project else None

    def get_project_name(self, obj) -> str | None:
        return obj.project.name if obj.project else None

    def get_team_code(self, obj) -> str | None:
        return obj.team.code if obj.team else None

    def get_team_name(self, obj) -> str | None:
        return obj.team.name if obj.team else None


class ResourcePlanDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    plan_type = serializers.CharField(read_only=True)
    plan_type_display = serializers.SerializerMethodField()
    financial_year_code = serializers.SerializerMethodField()
    financial_year_display = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_head = serializers.BooleanField(read_only=True)
    cloned_from_code = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()
    scope = serializers.SerializerMethodField()

    def get_plan_type_display(self, obj) -> str:
        return obj.get_plan_type_display()

    def get_financial_year_code(self, obj) -> str | None:
        return obj.financial_year.code if obj.financial_year else None

    def get_financial_year_display(self, obj) -> str | None:
        return obj.financial_year.short_fy if obj.financial_year else None

    def get_cloned_from_code(self, obj) -> str | None:
        return obj.cloned_from.code if obj.cloned_from else None

    def get_versions(self, obj) -> list[dict]:
        qs = obj.versions.order_by("-version")
        return ResourcePlanVersionSerializer(qs, many=True).data

    def get_scope(self, obj) -> dict | None:
        try:
            return ResourcePlanScopeSerializer(obj.scope).data
        except Exception:
            return None

    class Meta(AuditableSerializer.Meta):
        model = Plan
        fields = [
            "code",
            "name",
            "description",
            "plan_type",
            "plan_type_display",
            "financial_year_code",
            "financial_year_display",
            "is_active",
            "is_head",
            "cloned_from_code",
            "versions",
            "scope",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ResourcePlanCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    plan_type = serializers.ChoiceField(choices=PlanType.choices, required=True)
    financial_year_code = serializers.CharField(required=True)
    threshold_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        default=10.0,
        min_value=0,
        max_value=100,
    )
    is_active = serializers.BooleanField(default=True, required=False)
    is_head = serializers.BooleanField(default=False, required=False)
    scope_financial_year_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    scope_programme_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    scope_project_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    scope_team_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )

    def validate(self, attrs):
        for field in (
            "scope_financial_year_code",
            "scope_programme_code",
            "scope_project_code",
            "scope_team_code",
        ):
            if attrs.get(field) == "":
                attrs[field] = None
        return attrs


class ResourcePlanUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    threshold_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, min_value=0, max_value=100
    )
