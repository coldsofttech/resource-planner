from rest_framework import serializers

from apps.core.serializers import (
    AuditableSerializer,
    BaseSerializer,
    CodeSerializer,
    ListMixin,
    ReadMixin,
    UserMiniSerializer,
    WriteMixin,
)
from apps.projects.models import (
    Programme,
    Project,
    ProjectBudget,
    ProjectBudgetStatusHistory,
    ProjectCollaborator,
    ProjectEstimate,
    ProjectEstimateStatusHistory,
    ProjectFollower,
    ProjectLabel,
    ProjectStatus,
    ProjectSubStatus,
    ProjectTag,
    ProjectType,
)


class ProgrammeListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Programme
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProgrammeDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = Programme
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProgrammeCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProgrammeUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class ProjectTypeListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTypeDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectType
        fields = [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTypeCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=60, required=True)
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProjectTypeUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class ProjectStatusListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectStatus
        fields = [
            "code",
            "name",
            "sort_order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectStatusDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    sort_order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectStatus
        fields = [
            "code",
            "name",
            "sort_order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    main_status_code = serializers.CharField(source="main_status.code", read_only=True)
    main_status_name = serializers.CharField(source="main_status.name", read_only=True)
    order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectSubStatus
        fields = [
            "code",
            "name",
            "main_status_code",
            "main_status_name",
            "order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    main_status_code = serializers.CharField(source="main_status.code", read_only=True)
    main_status_name = serializers.CharField(source="main_status.name", read_only=True)
    order = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta(AuditableSerializer.Meta):
        model = ProjectSubStatus
        fields = [
            "code",
            "name",
            "main_status_code",
            "main_status_name",
            "order",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectSubStatusCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    is_active = serializers.BooleanField(default=True, required=False)


class ProjectSubStatusUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    is_active = serializers.BooleanField(required=False)


class ProjectSubStatusReorderSerializer(WriteMixin, serializers.Serializer):
    codes = serializers.ListField(
        child=serializers.CharField(), required=True, min_length=1
    )


class ProjectCollaboratorListSerializer(serializers.ModelSerializer):
    team_code = serializers.CharField(source="team.code", read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)
    added_on = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ProjectCollaborator
        fields = ["team_code", "team_name", "added_on"]


class ProjectListSerializer(ListMixin, CodeSerializer):
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    project_type_code = serializers.CharField(
        source="project_type.code", read_only=True
    )
    project_type_name = serializers.CharField(
        source="project_type.name", read_only=True
    )
    programme_code = serializers.CharField(
        source="programme.code", read_only=True, allow_null=True
    )
    programme_name = serializers.CharField(
        source="programme.name", read_only=True, allow_null=True
    )
    status_code = serializers.CharField(source="status.code", read_only=True)
    status_name = serializers.CharField(source="status.name", read_only=True)
    sub_status_code = serializers.CharField(
        source="sub_status.code", read_only=True, allow_null=True
    )
    sub_status_name = serializers.CharField(
        source="sub_status.name", read_only=True, allow_null=True
    )
    assigned_team_code = serializers.CharField(
        source="assigned_team.code", read_only=True, allow_null=True
    )
    assigned_team_name = serializers.CharField(
        source="assigned_team.name", read_only=True, allow_null=True
    )
    confidence = serializers.CharField(read_only=True, allow_null=True)
    priority = serializers.CharField(read_only=True, allow_null=True)
    start_date = serializers.DateField(read_only=True, allow_null=True)
    end_date = serializers.DateField(read_only=True, allow_null=True)
    commitment_date = serializers.DateField(read_only=True, allow_null=True)
    efforts_issued = serializers.BooleanField(read_only=True)
    run_cost_applies = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = Project
        fields = [
            "code",
            "name",
            "display_name",
            "description",
            "is_active",
            "project_type_code",
            "project_type_name",
            "programme_code",
            "programme_name",
            "status_code",
            "status_name",
            "sub_status_code",
            "sub_status_name",
            "assigned_team_code",
            "assigned_team_name",
            "confidence",
            "priority",
            "start_date",
            "end_date",
            "commitment_date",
            "efforts_issued",
            "run_cost_applies",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectDetailSerializer(ReadMixin, AuditableSerializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    project_type_code = serializers.CharField(
        source="project_type.code", read_only=True
    )
    project_type_name = serializers.CharField(
        source="project_type.name", read_only=True
    )
    programme_code = serializers.CharField(
        source="programme.code", read_only=True, allow_null=True
    )
    programme_name = serializers.CharField(
        source="programme.name", read_only=True, allow_null=True
    )
    status_code = serializers.CharField(source="status.code", read_only=True)
    status_name = serializers.CharField(source="status.name", read_only=True)
    sub_status_code = serializers.CharField(
        source="sub_status.code", read_only=True, allow_null=True
    )
    sub_status_name = serializers.CharField(
        source="sub_status.name", read_only=True, allow_null=True
    )
    assigned_team_code = serializers.CharField(
        source="assigned_team.code", read_only=True, allow_null=True
    )
    assigned_team_name = serializers.CharField(
        source="assigned_team.name", read_only=True, allow_null=True
    )
    confidence = serializers.CharField(read_only=True, allow_null=True)
    priority = serializers.CharField(read_only=True, allow_null=True)
    start_date = serializers.DateField(read_only=True, allow_null=True)
    end_date = serializers.DateField(read_only=True, allow_null=True)
    commitment_date = serializers.DateField(read_only=True, allow_null=True)
    efforts_issued = serializers.BooleanField(read_only=True)
    run_cost_applies = serializers.BooleanField(read_only=True)
    collaborators = ProjectCollaboratorListSerializer(many=True, read_only=True)
    is_following = serializers.SerializerMethodField()
    follower_code = serializers.SerializerMethodField()
    project_code_value = serializers.SerializerMethodField()

    def get_is_following(self, obj) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.followers.filter(user=request.user).exists()

    def get_follower_code(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        follower = obj.followers.filter(user=request.user).first()
        return follower.code if follower else None

    def get_project_code_value(self, obj) -> str | None:
        code = obj.codes.first()
        return code.value if code else None

    class Meta(AuditableSerializer.Meta):
        model = Project
        fields = [
            "code",
            "name",
            "display_name",
            "description",
            "is_active",
            "project_type_code",
            "project_type_name",
            "programme_code",
            "programme_name",
            "status_code",
            "status_name",
            "sub_status_code",
            "sub_status_name",
            "assigned_team_code",
            "assigned_team_name",
            "confidence",
            "priority",
            "start_date",
            "end_date",
            "commitment_date",
            "efforts_issued",
            "run_cost_applies",
            "collaborators",
            "is_following",
            "follower_code",
            "project_code_value",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectCreateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True)
    project_type_code = serializers.CharField(required=True)
    status_code = serializers.CharField(required=True)
    programme_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    sub_status_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    assigned_team_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    description = serializers.CharField(default="", required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True, required=False)
    confidence = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    priority = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    start_date = serializers.DateField(required=False, allow_null=True, default=None)
    end_date = serializers.DateField(required=False, allow_null=True, default=None)
    commitment_date = serializers.DateField(
        required=False, allow_null=True, default=None
    )
    efforts_issued = serializers.BooleanField(default=False, required=False)
    run_cost_applies = serializers.BooleanField(default=False, required=False)


class ProjectUpdateSerializer(WriteMixin, serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    project_type_code = serializers.CharField(required=False)
    status_code = serializers.CharField(required=False)
    programme_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    sub_status_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    assigned_team_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    confidence = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    priority = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    commitment_date = serializers.DateField(required=False, allow_null=True)
    efforts_issued = serializers.BooleanField(required=False)
    run_cost_applies = serializers.BooleanField(required=False)
    project_code_value = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class ProjectCollaboratorSerializer(BaseSerializer):
    team_code = serializers.CharField(required=True)


_LABEL_REGEX = r"^[A-Z0-9_]+$"
_LABEL_FORMAT_MSG = (
    "Label must contain only uppercase letters (A-Z), digits (0-9), "
    "and underscores (_)."
)


class ProjectLabelSerializer(ListMixin, CodeSerializer):
    label = serializers.CharField(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectLabel
        fields = [
            "code",
            "label",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectLabelCreateSerializer(WriteMixin, serializers.Serializer):
    label = serializers.RegexField(
        regex=_LABEL_REGEX,
        max_length=50,
        required=True,
        error_messages={"invalid": _LABEL_FORMAT_MSG},
    )
    is_default = serializers.BooleanField(default=False, required=False)


class ProjectLabelUpdateSerializer(WriteMixin, serializers.Serializer):
    label = serializers.RegexField(
        regex=_LABEL_REGEX,
        max_length=50,
        required=False,
        error_messages={"invalid": _LABEL_FORMAT_MSG},
    )
    is_default = serializers.BooleanField(required=False)


class ProjectTagSerializer(ListMixin, CodeSerializer):
    tag_code = serializers.CharField(source="tag.code", read_only=True)
    tag_name = serializers.CharField(source="tag.name", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    class Meta(CodeSerializer.Meta):
        model = ProjectTag
        fields = [
            "code",
            "tag_code",
            "tag_name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectTagCreateSerializer(WriteMixin, serializers.Serializer):
    tag_code = serializers.CharField(required=False, allow_blank=False)
    tag_name = serializers.CharField(required=False, allow_blank=False)

    def validate(self, data: dict) -> dict:
        if not data.get("tag_code") and not data.get("tag_name"):
            raise serializers.ValidationError(
                {"tag_name": "Either tag_code or tag_name is required."}
            )
        return data


class ProjectTagUpdateSerializer(WriteMixin, serializers.Serializer):
    tag_code = serializers.CharField(required=False)


class ProjectFollowerListSerializer(ListMixin, CodeSerializer):
    user_code = serializers.CharField(source="user.profile.code", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    created_by = UserMiniSerializer(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by = UserMiniSerializer(read_only=True, allow_null=True)

    def get_user_name(self, obj) -> str:
        parts = [obj.user.first_name, obj.user.last_name]
        return " ".join(p for p in parts if p) or obj.user.email

    class Meta(CodeSerializer.Meta):
        model = ProjectFollower
        fields = [
            "code",
            "user_code",
            "user_email",
            "user_name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class ProjectFollowerCreateSerializer(WriteMixin, serializers.Serializer):
    user_code = serializers.CharField(required=True)


class ProjectFollowerUpdateSerializer(WriteMixin, serializers.Serializer):
    user_code = serializers.CharField(required=False)


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
            "estimate_link",
            "approval_email_sent",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


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


class _FinancialYearInlineSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


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
