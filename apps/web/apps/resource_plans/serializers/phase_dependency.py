from rest_framework import serializers

from apps.core.serializers import ListMixin, ReadMixin, WriteMixin
from apps.resource_plans.constants import DependencyType


class PlanPhaseDependencySerializer(ReadMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    dependency_type = serializers.CharField(read_only=True)
    dependency_type_display = serializers.SerializerMethodField()
    lag_sprints = serializers.IntegerField(read_only=True)
    predecessor_phase_code = serializers.SerializerMethodField()
    predecessor_phase_name = serializers.SerializerMethodField()
    predecessor_project_name = serializers.SerializerMethodField()
    predecessor_team_name = serializers.SerializerMethodField()

    def get_dependency_type_display(self, obj) -> str:
        return obj.get_dependency_type_display()

    def get_predecessor_phase_code(self, obj) -> str:
        return obj.predecessor_phase.code

    def get_predecessor_phase_name(self, obj) -> str:
        return obj.predecessor_phase.name

    def get_predecessor_project_name(self, obj) -> str:
        return obj.predecessor_phase.plan_project_team.plan_project.project.name

    def get_predecessor_team_name(self, obj) -> str:
        return obj.predecessor_phase.plan_project_team.team.name


class PlanPhaseDependencyCreateSerializer(WriteMixin, serializers.Serializer):
    predecessor_phase_code = serializers.CharField(required=True)
    dependency_type = serializers.ChoiceField(
        choices=DependencyType.choices, required=True
    )
    lag_sprints = serializers.IntegerField(required=False, default=0)


class PlanPhaseDependencyUpdateSerializer(WriteMixin, serializers.Serializer):
    predecessor_phase_code = serializers.CharField(required=True)
    dependency_type = serializers.ChoiceField(
        choices=DependencyType.choices, required=True
    )
    lag_sprints = serializers.IntegerField(required=False, default=0)


class AvailablePredecessorPhaseSerializer(ListMixin, serializers.Serializer):
    code = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    project_name = serializers.SerializerMethodField()
    team_name = serializers.SerializerMethodField()

    def get_project_name(self, obj) -> str:
        return obj.plan_project_team.plan_project.project.name

    def get_team_name(self, obj) -> str:
        return obj.plan_project_team.team.name
