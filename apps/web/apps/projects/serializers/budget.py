from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import ProjectBudget, ProjectBudgetStatusHistory


class _BudgetRiskSerializer(serializers.Serializer):
    color = serializers.CharField(read_only=True)
    display = serializers.CharField(read_only=True)
    short = serializers.CharField(read_only=True)
    percentage = serializers.CharField(read_only=True)


class _FinancialYearInlineSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(source="long_fy", read_only=True)


class _EstimateVersionInlineSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    version_display = serializers.CharField(read_only=True)
    total_cost = serializers.FloatField(read_only=True)


class ProjectBudgetListSerializer(ListMixin, CodeSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    financial_year = _FinancialYearInlineSerializer(read_only=True)
    allocated_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    refined_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True, allow_null=True
    )
    actual_budget = serializers.FloatField(read_only=True)
    remaining_budget = serializers.FloatField(read_only=True, allow_null=True)
    estimate_version = _EstimateVersionInlineSerializer(read_only=True, allow_null=True)
    risk = _BudgetRiskSerializer(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectBudget
        fields = [
            "code",
            "project_code",
            "project_name",
            "financial_year",
            "allocated_budget",
            "refined_budget",
            "actual_budget",
            "remaining_budget",
            "estimate_version",
            "risk",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectBudgetDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    project_code = serializers.CharField(source="project.code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    financial_year = _FinancialYearInlineSerializer(read_only=True)
    allocated_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    refined_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True, allow_null=True
    )
    actual_budget = serializers.FloatField(read_only=True)
    remaining_budget = serializers.FloatField(read_only=True, allow_null=True)
    estimate_version = _EstimateVersionInlineSerializer(read_only=True, allow_null=True)
    risk = _BudgetRiskSerializer(read_only=True, allow_null=True)
    note = serializers.CharField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectBudget
        fields = [
            "code",
            "project_code",
            "project_name",
            "financial_year",
            "allocated_budget",
            "refined_budget",
            "actual_budget",
            "remaining_budget",
            "estimate_version",
            "risk",
            "note",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectBudgetCreateSerializer(WriteMixin, serializers.Serializer):
    financial_year_code = serializers.CharField(required=True)
    allocated_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=True
    )
    refined_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, default=None
    )
    estimate_version_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")


class ProjectBudgetUpdateSerializer(WriteMixin, serializers.Serializer):
    allocated_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False
    )
    refined_budget = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True
    )
    estimate_version_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    note = serializers.CharField(required=False, allow_blank=True)


class ProjectBudgetStatusHistorySerializer(serializers.ModelSerializer):
    previous_estimate_version = _EstimateVersionInlineSerializer(
        read_only=True, allow_null=True
    )
    new_estimate_version = _EstimateVersionInlineSerializer(
        read_only=True, allow_null=True
    )
    changed_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ProjectBudgetStatusHistory
        fields = [
            "id",
            "action",
            "previous_allocated_budget",
            "previous_refined_budget",
            "previous_estimate_version",
            "previous_total_cost",
            "new_allocated_budget",
            "new_refined_budget",
            "new_estimate_version",
            "new_total_cost",
            "note",
            "changed_on",
            "changed_by",
        ]


class ProjectBudgetLifetimeSerializer(serializers.Serializer):
    project_code = serializers.CharField(read_only=True)
    project_name = serializers.CharField(read_only=True)
    budget_count = serializers.IntegerField(read_only=True)
    total_allocated_budget = serializers.FloatField(read_only=True)
    total_refined_budget = serializers.FloatField(read_only=True, allow_null=True)
    total_actual_budget = serializers.FloatField(read_only=True)
    total_estimate_cost = serializers.FloatField(read_only=True, allow_null=True)
    total_remaining_budget = serializers.FloatField(read_only=True, allow_null=True)
    risk = _BudgetRiskSerializer(read_only=True, allow_null=True)
