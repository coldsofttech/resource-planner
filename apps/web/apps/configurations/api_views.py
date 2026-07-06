from apps.configurations.selectors import AI as AISelector
from apps.configurations.selectors import Auth as AuthSelector
from apps.configurations.selectors import PasswordPolicy as PasswordPolicySelector
from apps.configurations.serializers import (
    AIConfigSerializer,
    AIConfigUpdateSerializer,
    SecurityConfigSerializer,
    SecurityConfigUpdateSerializer,
)
from apps.configurations.services import AdminConfigurationService
from apps.core.viewsets import BaseViewSet

_CONFIG_MAP = {
    "is_ai_enabled": "AI_ENABLED",
    "ai_provider": "AI_PROVIDER",
    "ai_model": "AI_MODEL",
    "ai_anthropic_api_key": "AI_ANTHROPIC_API_KEY",
    "ai_bedrock_region": "AI_BEDROCK_REGION",
    "ai_bedrock_auth_mode": "AI_BEDROCK_AUTH_MODE",
    "ai_bedrock_iam_key": "AI_BEDROCK_IAM_KEY",
    "ai_bedrock_iam_secret": "AI_BEDROCK_IAM_SECRET",
}

_SECURITY_CONFIG_MAP = {
    "password_rotation_days": "PASSWORD_ROTATION_DAYS",
    "password_min_length": "PASSWORD_MIN_LENGTH",
    "password_require_uppercase": "PASSWORD_REQUIRE_UPPERCASE",
    "password_require_lowercase": "PASSWORD_REQUIRE_LOWERCASE",
    "password_require_digits": "PASSWORD_REQUIRE_DIGITS",
    "password_require_special": "PASSWORD_REQUIRE_SPECIAL",
    "password_history_count": "PASSWORD_HISTORY_COUNT",
    "session_timeout_minutes": "SESSION_TIMEOUT_MINUTES",
}


def _current_config() -> dict:
    return {
        "is_ai_enabled": AISelector.is_ai_enabled(),
        "ai_provider": AISelector.get_ai_provider(),
        "ai_model": AISelector.get_ai_model(),
        "ai_anthropic_api_key": AISelector.get_anthropic_api_key(),
        "ai_bedrock_region": AISelector.get_bedrock_region(),
        "ai_bedrock_auth_mode": AISelector.get_bedrock_auth_mode(),
        "ai_bedrock_iam_key": AISelector.get_bedrock_iam_key(),
        "ai_bedrock_iam_secret": AISelector.get_bedrock_iam_secret(),
    }


class AIConfigViewSet(BaseViewSet):
    def retrieve(self, request):
        raw = _current_config()
        serializer = AIConfigSerializer(raw)
        return self.response(data=serializer.data)

    def partial_update(self, request):
        serializer = AIConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        svc = AdminConfigurationService(user=request.user, request=request)
        for field, code in _CONFIG_MAP.items():
            if field in serializer.validated_data:
                svc.set_config(config_code=code, value=serializer.validated_data[field])

        raw = _current_config()
        return self.response(
            data=AIConfigSerializer(raw).data,
            message="AI configuration updated successfully.",
        )


def _current_security_config() -> dict:
    return {
        "password_rotation_days": PasswordPolicySelector.get_rotation_days(),
        "password_min_length": PasswordPolicySelector.get_min_length(),
        "password_require_uppercase": PasswordPolicySelector.require_uppercase(),
        "password_require_lowercase": PasswordPolicySelector.require_lowercase(),
        "password_require_digits": PasswordPolicySelector.require_digits(),
        "password_require_special": PasswordPolicySelector.require_special(),
        "password_history_count": PasswordPolicySelector.get_history_count(),
        "session_timeout_minutes": AuthSelector.get_session_timeout_minutes(),
    }


class SecurityConfigViewSet(BaseViewSet):
    def retrieve(self, request):
        raw = _current_security_config()
        serializer = SecurityConfigSerializer(raw)
        return self.response(data=serializer.data)

    def partial_update(self, request):
        serializer = SecurityConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        svc = AdminConfigurationService(user=request.user, request=request)
        for field, code in _SECURITY_CONFIG_MAP.items():
            if field in serializer.validated_data:
                svc.set_config(config_code=code, value=serializer.validated_data[field])

        raw = _current_security_config()
        return self.response(
            data=SecurityConfigSerializer(raw).data,
            message="Security configuration updated successfully.",
        )
