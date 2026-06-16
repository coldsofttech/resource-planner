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
from apps.projects.models import Project, ProjectCollaborator


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
