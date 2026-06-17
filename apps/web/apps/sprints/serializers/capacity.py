from rest_framework import serializers


class CapacityMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    def get_team(self, obj) -> str:
        assignment = obj.team_assignments.first()
        if assignment:
            return assignment.team.name
        return ""

    def get_location(self, obj) -> str:
        try:
            return obj.profile.location.name if obj.profile.location else ""
        except Exception:
            return ""


class CapacitySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    member = CapacityMemberSerializer(read_only=True)
    working_days = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True
    )
    holiday_days = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True
    )
    leave_days = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True
    )
    net_capacity = serializers.DecimalField(
        max_digits=6, decimal_places=1, read_only=True
    )
    updated_at = serializers.DateTimeField(read_only=True)
