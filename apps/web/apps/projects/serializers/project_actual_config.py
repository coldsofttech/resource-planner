from rest_framework import serializers

from apps.core.serializers import BaseSerializer


class ProjectActualConfigSerializer(BaseSerializer):
    ignore_risk = serializers.BooleanField(required=False)
    ignore_prev_fy_actuals = serializers.BooleanField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
