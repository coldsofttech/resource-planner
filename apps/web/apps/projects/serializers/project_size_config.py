from rest_framework import serializers


class ProjectSizeConfigSerializer(serializers.Serializer):
    xs_max_amount = serializers.IntegerField(min_value=1)
    s_max_amount = serializers.IntegerField(min_value=1)
    m_max_amount = serializers.IntegerField(min_value=1)
    l_max_amount = serializers.IntegerField(min_value=1)

    def validate(self, data: dict) -> dict:
        xsmall = data.get("xs_max_amount", 0)
        small = data.get("s_max_amount", 0)
        medium = data.get("m_max_amount", 0)
        large = data.get("l_max_amount", 0)

        if xsmall >= small:
            raise serializers.ValidationError(
                {"s_max_amount": "S max amount must be greater than XS max amount."}
            )
        if small >= medium:
            raise serializers.ValidationError(
                {"m_max_amount": "M max amount must be greater than S max amount."}
            )
        if medium >= large:
            raise serializers.ValidationError(
                {"l_max_amount": "L max amount must be greater than M max amount."}
            )
        return data
