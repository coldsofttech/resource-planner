from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.reports.constants import (
    AggregationFunction,
    FilterOperator,
    ReportVisualization,
    SharePermission,
)
from apps.reports.models import (
    CustomReport,
    DemandCapacityReportConfig,
    KPIEstimateAccuracyConfig,
    Report,
)


class ReportListSerializer(ListMixin, CodeSerializer):
    slug = serializers.SlugField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Report
        fields = [
            "code",
            "slug",
            "name",
            "description",
            "category",
            "icon",
            "is_active",
            "sort_order",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ReportDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    icon = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Report
        fields = [
            "code",
            "slug",
            "name",
            "description",
            "category",
            "icon",
            "is_active",
            "sort_order",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ReportCreateSerializer(WriteMixin, serializers.Serializer):
    slug = serializers.SlugField(max_length=100, required=True)
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    category = serializers.CharField(
        max_length=100, default="", required=False, allow_blank=True
    )
    icon = serializers.CharField(
        max_length=50, default="bi-bar-chart", required=False, allow_blank=True
    )
    sort_order = serializers.IntegerField(default=0, required=False)
    is_active = serializers.BooleanField(default=True, required=False)


class ReportUpdateSerializer(WriteMixin, serializers.Serializer):
    slug = serializers.SlugField(max_length=100, required=False)
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    icon = serializers.CharField(max_length=50, required=False, allow_blank=True)
    sort_order = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)


class CustomReportOwnershipMixin:
    """Adds `is_readonly` — true when the current user cannot edit/delete."""

    context: dict

    def get_is_readonly(self, obj) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return True
        return not obj.can_edit(user)


class CustomReportListSerializer(CustomReportOwnershipMixin, ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    owner = UserMiniSerializer(read_only=True)
    data_source = serializers.CharField(read_only=True)
    visualization = serializers.CharField(read_only=True)
    is_shared = serializers.BooleanField(read_only=True)
    is_readonly = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = CustomReport
        fields = [
            "code",
            "name",
            "description",
            "owner",
            "data_source",
            "visualization",
            "is_shared",
            "is_readonly",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class CustomReportDetailSerializer(
    CustomReportOwnershipMixin, ReadMixin, AuditableSerializer
):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    owner = UserMiniSerializer(read_only=True)
    data_source = serializers.CharField(read_only=True)
    visualization = serializers.CharField(read_only=True)
    config = serializers.JSONField(read_only=True)
    is_shared = serializers.BooleanField(read_only=True)
    is_readonly = serializers.SerializerMethodField()

    class Meta(AuditableSerializer.Meta):
        model = CustomReport
        fields = [
            "code",
            "name",
            "description",
            "owner",
            "data_source",
            "visualization",
            "config",
            "is_shared",
            "is_readonly",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


def _validate_data_source_choice(value: str) -> str:
    from apps.reports.data_sources import get_data_source

    if value and get_data_source(value) is None:
        raise serializers.ValidationError(f"Unknown data source '{value}'.")
    return value


class CustomReportCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_shared = serializers.BooleanField(default=False, required=False)
    data_source = serializers.CharField(
        max_length=50, default="", required=False, allow_blank=True
    )
    visualization = serializers.ChoiceField(
        choices=ReportVisualization.CHOICES,
        default=ReportVisualization.TABLE,
        required=False,
    )
    config = serializers.JSONField(default=dict, required=False)

    def validate_data_source(self, value: str) -> str:
        return _validate_data_source_choice(value)


class CustomReportUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_shared = serializers.BooleanField(required=False)
    data_source = serializers.CharField(max_length=50, required=False, allow_blank=True)
    visualization = serializers.ChoiceField(
        choices=ReportVisualization.CHOICES, required=False
    )
    config = serializers.JSONField(required=False)

    def validate_data_source(self, value: str) -> str:
        return _validate_data_source_choice(value)


class CustomReportFilterSerializer(serializers.Serializer):
    field = serializers.CharField(max_length=200, required=True)
    operator = serializers.ChoiceField(choices=FilterOperator.CHOICES, required=True)
    value = serializers.JSONField(required=False, allow_null=True)


class CustomReportValueSerializer(serializers.Serializer):
    field = serializers.CharField(max_length=200, required=True)
    aggregation = serializers.ChoiceField(
        choices=AggregationFunction.CHOICES, required=True
    )


class CustomReportSortSerializer(serializers.Serializer):
    field = serializers.CharField(max_length=200, required=True)
    direction = serializers.ChoiceField(
        choices=["asc", "desc"], default="asc", required=False
    )


class CustomReportConfigSerializer(serializers.Serializer):
    fields = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False, default=list
    )
    filters = CustomReportFilterSerializer(many=True, required=False, default=list)
    values = CustomReportValueSerializer(many=True, required=False, default=list)
    axis = serializers.CharField(
        max_length=200, required=False, allow_blank=True, allow_null=True
    )
    legend = serializers.CharField(
        max_length=200, required=False, allow_blank=True, allow_null=True
    )
    sort_by = CustomReportSortSerializer(many=True, required=False, default=list)


class CustomReportPreviewRequestSerializer(serializers.Serializer):
    data_source = serializers.CharField(max_length=50, required=True)
    visualization = serializers.ChoiceField(
        choices=ReportVisualization.CHOICES, required=True
    )
    config = CustomReportConfigSerializer(required=False)

    def validate_data_source(self, value: str) -> str:
        return _validate_data_source_choice(value)


class CustomReportExecuteRequestSerializer(serializers.Serializer):
    data_source = serializers.CharField(max_length=50, required=False, allow_blank=True)
    visualization = serializers.ChoiceField(
        choices=ReportVisualization.CHOICES, required=False
    )
    config = CustomReportConfigSerializer(required=False)

    def validate_data_source(self, value: str) -> str:
        return _validate_data_source_choice(value)


class DataSourceFieldSerializer(serializers.Serializer):
    key = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    filterable = serializers.BooleanField(read_only=True)
    groupable = serializers.BooleanField(read_only=True)
    aggregatable = serializers.BooleanField(read_only=True)
    choices = serializers.SerializerMethodField()

    def get_choices(self, obj) -> list[dict] | None:
        if not obj.choices:
            return None
        return [{"value": value, "label": label} for value, label in obj.choices]


class DataSourceSerializer(serializers.Serializer):
    key = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    fields = DataSourceFieldSerializer(many=True, read_only=True)


class CustomReportShareCreateSerializer(WriteMixin, serializers.Serializer):
    member_code = serializers.CharField(max_length=50, required=True)
    permission = serializers.ChoiceField(
        choices=SharePermission.CHOICES, default=SharePermission.VIEW, required=False
    )


class CustomReportShareListSerializer(serializers.Serializer):
    member_code = serializers.CharField(source="user.profile.code", read_only=True)
    member_name = serializers.CharField(
        source="user.profile.display_name", read_only=True
    )
    email = serializers.CharField(source="user.email", read_only=True)
    permission = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class WeeklyWinsQuerySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["date", "week"], required=True)
    date = serializers.DateField(required=False)
    win = serializers.CharField(max_length=50, required=False)

    def validate(self, attrs):
        mode = attrs.get("mode")
        if mode == "date" and not attrs.get("date"):
            raise serializers.ValidationError(
                {"date": "This field is required when mode is 'date'."}
            )
        if mode == "week" and not attrs.get("win"):
            raise serializers.ValidationError(
                {"win": "This field is required when mode is 'week'."}
            )
        return attrs


class WeeklyWinsEntrySerializer(serializers.Serializer):
    team = serializers.CharField(read_only=True)
    week = serializers.CharField(read_only=True)
    date_range = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)


class WeeklyWinsWinSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    week_number = serializers.IntegerField(read_only=True)
    week = serializers.CharField(read_only=True)
    date_range = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)


class WeeklyWinsDataSerializer(serializers.Serializer):
    win = WeeklyWinsWinSerializer(read_only=True)
    entries = WeeklyWinsEntrySerializer(read_only=True, many=True)


class SprintForecastVsActualsQuerySerializer(serializers.Serializer):
    sprint = serializers.CharField(max_length=50, required=True)
    team = serializers.CharField(max_length=50, required=False, allow_blank=True)


class SprintForecastVsActualsRowSerializer(serializers.Serializer):
    team = serializers.CharField(read_only=True)
    engineer = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    project = serializers.CharField(read_only=True)
    programme = serializers.CharField(read_only=True)
    finance_type = serializers.CharField(read_only=True)
    forecast_days = serializers.CharField(read_only=True)
    actual_days = serializers.CharField(read_only=True)
    variance_days = serializers.CharField(read_only=True)


class SprintForecastVsActualsGroupRowSerializer(serializers.Serializer):
    team = serializers.CharField(read_only=True, required=False)
    engineer = serializers.CharField(read_only=True, required=False)
    label = serializers.CharField(read_only=True, required=False)
    project = serializers.CharField(read_only=True, required=False)
    programme = serializers.CharField(read_only=True, required=False)
    finance_type = serializers.CharField(read_only=True, required=False)
    forecast_days = serializers.CharField(read_only=True)
    actual_days = serializers.CharField(read_only=True)
    variance_days = serializers.CharField(read_only=True)


class SprintForecastVsActualsGroupedSerializer(serializers.Serializer):
    label = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)
    project = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)
    programme = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)
    team = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)
    engineer = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)
    finance_type = SprintForecastVsActualsGroupRowSerializer(read_only=True, many=True)


class SprintForecastVsActualsTotalsSerializer(serializers.Serializer):
    forecast_days = serializers.CharField(read_only=True)
    actual_days = serializers.CharField(read_only=True)
    variance_days = serializers.CharField(read_only=True)


class SprintForecastVsActualsSprintSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    financial_year = serializers.CharField(read_only=True)


class SprintForecastVsActualsTeamSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class SprintForecastVsActualsDataSerializer(serializers.Serializer):
    sprint = SprintForecastVsActualsSprintSerializer(read_only=True)
    team = SprintForecastVsActualsTeamSerializer(read_only=True, allow_null=True)
    has_forecast = serializers.BooleanField(read_only=True)
    has_actuals = serializers.BooleanField(read_only=True)
    totals = SprintForecastVsActualsTotalsSerializer(read_only=True)
    all_rows = SprintForecastVsActualsRowSerializer(read_only=True, many=True)
    grouped = SprintForecastVsActualsGroupedSerializer(read_only=True)


class MonthlyWinsQuerySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50, required=True)


class MonthlyWinsMonthlyWinSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)


class MonthlyWinsPhase1RowSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    phase1_votes = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    team = serializers.CharField(read_only=True)
    week = serializers.CharField(read_only=True)
    date_range = serializers.CharField(read_only=True)
    win = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    category_display = serializers.CharField(read_only=True)


class MonthlyWinsPhase2EntrySerializer(serializers.Serializer):
    team = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    rank = serializers.IntegerField(read_only=True)
    vote_count = serializers.IntegerField(read_only=True)


class MonthlyWinsPhase2CategorySerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    entries = MonthlyWinsPhase2EntrySerializer(read_only=True, many=True)


class MonthlyWinsPhase2DataSerializer(serializers.Serializer):
    delivery = MonthlyWinsPhase2CategorySerializer(read_only=True)
    operational_excellence = MonthlyWinsPhase2CategorySerializer(read_only=True)


class MonthlyWinsDataSerializer(serializers.Serializer):
    monthly_win = MonthlyWinsMonthlyWinSerializer(read_only=True)
    phase1 = MonthlyWinsPhase1RowSerializer(read_only=True, many=True)
    phase2 = MonthlyWinsPhase2DataSerializer(read_only=True)


class DemandCapacityReportConfigListSerializer(ListMixin, CodeSerializer):
    plan = serializers.SlugRelatedField(slug_field="code", read_only=True)
    version = serializers.IntegerField(source="plan_version.version", read_only=True)
    programme = serializers.SlugRelatedField(slug_field="code", read_only=True)
    programme_name = serializers.CharField(source="programme.name", read_only=True)
    category = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = DemandCapacityReportConfig
        fields = [
            "code",
            "plan",
            "version",
            "programme",
            "programme_name",
            "category",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class DemandCapacityReportConfigDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    plan = serializers.SlugRelatedField(slug_field="code", read_only=True)
    version = serializers.IntegerField(source="plan_version.version", read_only=True)
    programme = serializers.SlugRelatedField(slug_field="code", read_only=True)
    programme_name = serializers.CharField(source="programme.name", read_only=True)
    category = serializers.CharField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = DemandCapacityReportConfig
        fields = [
            "code",
            "plan",
            "version",
            "programme",
            "programme_name",
            "category",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class DemandCapacityReportConfigCreateSerializer(WriteMixin, serializers.Serializer):
    plan_code = serializers.CharField(max_length=50, required=True)
    version = serializers.IntegerField(required=True)
    programme_code = serializers.CharField(max_length=50, required=True)
    category = serializers.CharField(max_length=100, required=True, allow_blank=False)


class DemandCapacityReportConfigUpdateSerializer(WriteMixin, serializers.Serializer):
    programme_code = serializers.CharField(max_length=50, required=False)
    category = serializers.CharField(max_length=100, required=False, allow_blank=False)


class DemandVsCapacityQuerySerializer(serializers.Serializer):
    plan = serializers.CharField(max_length=50, required=True)
    version = serializers.IntegerField(required=True)
    team = serializers.CharField(max_length=50, required=False, allow_blank=True)
    employment_type = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )


class DemandVsCapacityRowSerializer(serializers.Serializer):
    key = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    values = serializers.DictField(read_only=True)


class DemandVsCapacityScopeSerializer(serializers.Serializer):
    rows = DemandVsCapacityRowSerializer(read_only=True, many=True)


class DemandVsCapacityTeamBlockSerializer(serializers.Serializer):
    team = SprintForecastVsActualsTeamSerializer(read_only=True)
    rows = DemandVsCapacityRowSerializer(read_only=True, many=True)


class DemandVsCapacityPlanSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class DemandVsCapacityVersionSerializer(serializers.Serializer):
    number = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)


class DemandVsCapacityEmploymentTypeSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class DemandVsCapacityDataSerializer(serializers.Serializer):
    plan = DemandVsCapacityPlanSerializer(read_only=True)
    version = DemandVsCapacityVersionSerializer(read_only=True)
    team = SprintForecastVsActualsTeamSerializer(read_only=True, allow_null=True)
    employment_type = DemandVsCapacityEmploymentTypeSerializer(
        read_only=True, allow_null=True
    )
    has_allocation_set = serializers.BooleanField(read_only=True)
    months = serializers.ListField(child=serializers.CharField(), read_only=True)
    month_labels = serializers.DictField(read_only=True)
    categories = serializers.ListField(child=serializers.CharField(), read_only=True)
    overall = DemandVsCapacityScopeSerializer(read_only=True)
    teams = DemandVsCapacityTeamBlockSerializer(read_only=True, many=True)


class KPIEstimateAccuracyConfigListSerializer(ListMixin, CodeSerializer):
    project = serializers.SlugRelatedField(slug_field="code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    month = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = KPIEstimateAccuracyConfig
        fields = [
            "code",
            "project",
            "project_name",
            "month",
            "comment",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class KPIEstimateAccuracyConfigDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    project = serializers.SlugRelatedField(slug_field="code", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    month = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = KPIEstimateAccuracyConfig
        fields = [
            "code",
            "project",
            "project_name",
            "month",
            "comment",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class KPIEstimateAccuracyConfigCreateSerializer(WriteMixin, serializers.Serializer):
    project_code = serializers.CharField(max_length=50, required=True)
    month = serializers.RegexField(r"^\d{4}-\d{2}$", required=True)
    comment = serializers.CharField(required=True, allow_blank=False)


class KPIEstimateAccuracyConfigUpdateSerializer(WriteMixin, serializers.Serializer):
    comment = serializers.CharField(required=True, allow_blank=False)


class KPIEstimateAccuracyQuerySerializer(serializers.Serializer):
    fy = serializers.CharField(max_length=50, required=True)
    month = serializers.RegexField(r"^\d{4}-\d{2}$", required=True)


class KPIEstimateAccuracyRowSerializer(serializers.Serializer):
    project_code = serializers.CharField(read_only=True)
    project = serializers.CharField(read_only=True)
    programme = serializers.CharField(read_only=True)
    team = serializers.CharField(read_only=True)
    collaborators = serializers.ListField(child=serializers.CharField(), read_only=True)
    collaborators_display = serializers.CharField(read_only=True)
    estimate_value = serializers.CharField(read_only=True)
    estimate_value_with_contingency = serializers.CharField(read_only=True)
    total_cost_till_date = serializers.CharField(read_only=True)
    tshirt_size = serializers.CharField(read_only=True)
    accuracy_pct = serializers.FloatField(read_only=True, allow_null=True)
    band = serializers.CharField(read_only=True)
    band_key = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True)


class KPIEstimateAccuracyFySerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class KPIEstimateAccuracyDataSerializer(serializers.Serializer):
    fy = KPIEstimateAccuracyFySerializer(read_only=True)
    month = serializers.CharField(read_only=True)
    month_label = serializers.CharField(read_only=True)
    rows = KPIEstimateAccuracyRowSerializer(read_only=True, many=True)
    band_labels = serializers.DictField(read_only=True)
    band_order = serializers.ListField(child=serializers.CharField(), read_only=True)
    charts = serializers.DictField(read_only=True)


class MonthlyFinanceReportQuerySerializer(serializers.Serializer):
    fy = serializers.CharField(max_length=50, required=True)
    month = serializers.RegexField(r"^\d{4}-\d{2}$", required=True)


class MonthlyFinanceReportSprintSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    has_actuals = serializers.BooleanField(read_only=True)


class MonthlyFinanceReportRowSerializer(serializers.Serializer):
    project_code = serializers.CharField(read_only=True)
    project = serializers.CharField(read_only=True)
    programme = serializers.CharField(read_only=True)
    total_days = serializers.CharField(read_only=True)
    total_cost = serializers.CharField(read_only=True)


class MonthlyFinanceReportTotalsSerializer(serializers.Serializer):
    project_count = serializers.IntegerField(read_only=True)
    total_days = serializers.CharField(read_only=True)
    total_cost = serializers.CharField(read_only=True)


class MonthlyFinanceReportDataSerializer(serializers.Serializer):
    fy = KPIEstimateAccuracyFySerializer(read_only=True)
    month = serializers.CharField(read_only=True)
    month_label = serializers.CharField(read_only=True)
    sprints = MonthlyFinanceReportSprintSerializer(read_only=True, many=True)
    is_complete = serializers.BooleanField(read_only=True)
    rows = MonthlyFinanceReportRowSerializer(read_only=True, many=True)
    totals = MonthlyFinanceReportTotalsSerializer(read_only=True)
