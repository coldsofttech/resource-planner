from rest_framework import serializers


class ProjectSizeConfigSerializer(serializers.Serializer):
    xs_max_amount = serializers.IntegerField(min_value=1, required=False)
    s_max_amount = serializers.IntegerField(min_value=1, required=False)
    m_max_amount = serializers.IntegerField(min_value=1, required=False)
    l_max_amount = serializers.IntegerField(min_value=1, required=False)
    budget_risk_threshold = serializers.FloatField(min_value=0, required=False)
    xs_budget_variance = serializers.FloatField(min_value=0, required=False)
    s_budget_variance = serializers.FloatField(min_value=0, required=False)
    m_budget_variance = serializers.FloatField(min_value=0, required=False)
    l_budget_variance = serializers.FloatField(min_value=0, required=False)
    xl_budget_variance = serializers.FloatField(min_value=0, required=False)

    def validate(self, data: dict) -> dict:
        xsmall = data.get("xs_max_amount")
        small = data.get("s_max_amount")
        medium = data.get("m_max_amount")
        large = data.get("l_max_amount")

        if xsmall is not None and small is not None and xsmall >= small:
            raise serializers.ValidationError(
                {"s_max_amount": "S max amount must be greater than XS max amount."}
            )
        if small is not None and medium is not None and small >= medium:
            raise serializers.ValidationError(
                {"m_max_amount": "M max amount must be greater than S max amount."}
            )
        if medium is not None and large is not None and medium >= large:
            raise serializers.ValidationError(
                {"l_max_amount": "L max amount must be greater than M max amount."}
            )
        return data
