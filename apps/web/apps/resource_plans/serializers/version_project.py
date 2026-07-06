from rest_framework import serializers

from apps.core.serializers import ListMixin, ReadMixin, UserMiniSerializer, WriteMixin
from apps.projects.models import Project
from apps.resource_plans.constants import Basis, Confidence, Priority


class UnmappedProjectSerializer(ListMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    programme_name = serializers.SerializerMethodField()

    def get_programme_name(self, obj: Project) -> str | None:
        return obj.programme.name if obj.programme_id else None


class PlanVersionProjectCreateSerializer(WriteMixin, serializers.Serializer):
    project_code = serializers.CharField(required=True)
    basis = serializers.ChoiceField(choices=Basis.choices, required=True)
    estimate_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    basis_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    priority_override = serializers.ChoiceField(
        choices=Priority.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    confidence_override = serializers.ChoiceField(
        choices=Confidence.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )

    def validate(self, attrs):
        basis = attrs.get("basis")
        if basis == Basis.ESTIMATE and not attrs.get("estimate_code"):
            raise serializers.ValidationError(
                {"estimate_code": "An estimate must be selected."}
            )
        if basis == Basis.CUSTOM and attrs.get("basis_amount") in (None, ""):
            raise serializers.ValidationError(
                {"basis_amount": "A basis amount is required."}
            )
        for field in ("priority_override", "confidence_override"):
            if attrs.get(field) == "":
                attrs[field] = None
        return attrs


class PlanVersionProjectListSerializer(ListMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    project_code = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    programme_name = serializers.SerializerMethodField()
    basis = serializers.CharField(read_only=True)
    basis_display = serializers.SerializerMethodField()
    basis_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    days_required = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    effective_priority = serializers.CharField(read_only=True)
    effective_confidence = serializers.CharField(read_only=True)
    resync_hidden = serializers.BooleanField(read_only=True)

    def get_project_code(self, obj) -> str:
        return obj.project.code

    def get_project_name(self, obj) -> str:
        return obj.project.name

    def get_programme_name(self, obj) -> str | None:
        return obj.project.programme.name if obj.project.programme_id else None

    def get_basis_display(self, obj) -> str:
        return obj.get_basis_display()


class PlanVersionProjectDetailSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    project_code = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    basis = serializers.CharField(read_only=True)
    basis_display = serializers.SerializerMethodField()
    basis_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    days_required = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    effective_priority = serializers.CharField(read_only=True)
    effective_confidence = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_project_code(self, obj) -> str:
        return obj.project.code

    def get_project_name(self, obj) -> str:
        return obj.project.name

    def get_basis_display(self, obj) -> str:
        return obj.get_basis_display()


class PlanVersionProjectConfigSerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    project_code = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    basis = serializers.CharField(read_only=True)
    basis_display = serializers.SerializerMethodField()
    basis_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    basis_synced_at = serializers.DateTimeField(read_only=True, allow_null=True)
    estimate_code = serializers.SerializerMethodField()
    priority_override = serializers.CharField(read_only=True, allow_null=True)
    effective_priority = serializers.CharField(read_only=True, allow_null=True)
    confidence_override = serializers.CharField(read_only=True, allow_null=True)
    effective_confidence = serializers.CharField(read_only=True, allow_null=True)
    start_sprint_code = serializers.SerializerMethodField()
    end_sprint_code = serializers.SerializerMethodField()
    dates_strict = serializers.BooleanField(read_only=True)

    def get_project_code(self, obj) -> str:
        return obj.project.code

    def get_project_name(self, obj) -> str:
        return obj.project.name

    def get_basis_display(self, obj) -> str:
        return obj.get_basis_display()

    def get_estimate_code(self, obj) -> str | None:
        return obj.snapshotted_estimate.code if obj.snapshotted_estimate_id else None

    def get_start_sprint_code(self, obj) -> str | None:
        return obj.start_sprint.code if obj.start_sprint_id else None

    def get_end_sprint_code(self, obj) -> str | None:
        return obj.end_sprint.code if obj.end_sprint_id else None


class PlanVersionProjectConfigUpdateSerializer(WriteMixin, serializers.Serializer):
    basis = serializers.ChoiceField(choices=Basis.choices, required=True)
    estimate_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    basis_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        default=None,
        min_value=0,
    )
    priority_override = serializers.ChoiceField(
        choices=Priority.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    confidence_override = serializers.ChoiceField(
        choices=Confidence.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
        default=None,
    )
    start_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    end_sprint_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    dates_strict = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        basis = attrs.get("basis")
        if basis == Basis.ESTIMATE and not attrs.get("estimate_code"):
            raise serializers.ValidationError(
                {"estimate_code": "An estimate must be selected."}
            )
        if basis == Basis.CUSTOM and attrs.get("basis_amount") in (None, ""):
            raise serializers.ValidationError(
                {"basis_amount": "A basis amount is required."}
            )
        for field in (
            "priority_override",
            "confidence_override",
            "start_sprint_code",
            "end_sprint_code",
        ):
            if attrs.get(field) == "":
                attrs[field] = None
        return attrs


class ProjectBudgetLookupSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    financial_year_display = serializers.SerializerMethodField()
    actual_budget = serializers.FloatField(read_only=True)

    def get_financial_year_display(self, obj) -> str | None:
        return obj.financial_year.short_fy if obj.financial_year else None
