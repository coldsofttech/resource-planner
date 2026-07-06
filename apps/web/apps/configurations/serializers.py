from rest_framework import serializers

_AI_PROVIDERS = ["anthropic", "bedrock"]
_AI_BEDROCK_AUTH_MODES = ["role", "user"]


class AIConfigSerializer(serializers.Serializer):
    """Read serializer — masks secret fields."""

    is_ai_enabled = serializers.BooleanField()
    ai_provider = serializers.CharField(allow_blank=True)
    ai_model = serializers.CharField(allow_blank=True)
    ai_anthropic_api_key = serializers.SerializerMethodField()
    ai_bedrock_region = serializers.CharField(allow_blank=True)
    ai_bedrock_auth_mode = serializers.CharField(allow_blank=True)
    ai_bedrock_iam_key = serializers.SerializerMethodField()
    ai_bedrock_iam_secret = serializers.SerializerMethodField()

    def get_ai_anthropic_api_key(self, obj: dict) -> str:
        return "[set]" if obj.get("ai_anthropic_api_key") else ""

    def get_ai_bedrock_iam_key(self, obj: dict) -> str:
        return "[set]" if obj.get("ai_bedrock_iam_key") else ""

    def get_ai_bedrock_iam_secret(self, obj: dict) -> str:
        return "[set]" if obj.get("ai_bedrock_iam_secret") else ""


class AIConfigUpdateSerializer(serializers.Serializer):
    """Write serializer — accepts partial updates."""

    is_ai_enabled = serializers.BooleanField(required=False)
    ai_provider = serializers.ChoiceField(
        choices=_AI_PROVIDERS, allow_blank=True, required=False
    )
    ai_model = serializers.CharField(max_length=256, allow_blank=True, required=False)
    ai_anthropic_api_key = serializers.CharField(
        max_length=512, allow_blank=True, required=False
    )
    ai_bedrock_region = serializers.CharField(
        max_length=64, allow_blank=True, required=False
    )
    ai_bedrock_auth_mode = serializers.ChoiceField(
        choices=_AI_BEDROCK_AUTH_MODES, allow_blank=True, required=False
    )
    ai_bedrock_iam_key = serializers.CharField(
        max_length=256, allow_blank=True, required=False
    )
    ai_bedrock_iam_secret = serializers.CharField(
        max_length=512, allow_blank=True, required=False
    )


class SecurityConfigSerializer(serializers.Serializer):
    """Read serializer for password policy + session settings."""

    password_rotation_days = serializers.IntegerField()
    password_min_length = serializers.IntegerField()
    password_require_uppercase = serializers.BooleanField()
    password_require_lowercase = serializers.BooleanField()
    password_require_digits = serializers.BooleanField()
    password_require_special = serializers.BooleanField()
    password_history_count = serializers.IntegerField()
    session_timeout_minutes = serializers.IntegerField()


class SecurityConfigUpdateSerializer(serializers.Serializer):
    """Write serializer — accepts partial updates."""

    password_rotation_days = serializers.IntegerField(min_value=0, required=False)
    password_min_length = serializers.IntegerField(min_value=1, required=False)
    password_require_uppercase = serializers.BooleanField(required=False)
    password_require_lowercase = serializers.BooleanField(required=False)
    password_require_digits = serializers.BooleanField(required=False)
    password_require_special = serializers.BooleanField(required=False)
    password_history_count = serializers.IntegerField(min_value=0, required=False)
    session_timeout_minutes = serializers.IntegerField(min_value=0, required=False)
