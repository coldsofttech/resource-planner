from rest_framework import serializers

from apps.core.serializers import BaseSerializer, WriteMixin
from apps.users.constants import ThemeChoices


class LoginSerializer(WriteMixin, BaseSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=1)


class ForgotPasswordRequestSerializer(WriteMixin, BaseSerializer):
    email = serializers.EmailField()


class ForgotPasswordVerifySerializer(WriteMixin, BaseSerializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class RegisterSerializer(WriteMixin, BaseSerializer):
    """Structural validation only — password strength is enforced by
    PasswordPolicyService in the service layer, since it is config-driven."""

    first_name = serializers.CharField(min_length=1, max_length=150)
    last_name = serializers.CharField(min_length=1, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=1)
    confirm_password = serializers.CharField(min_length=1)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class ForgotPasswordResetSerializer(WriteMixin, BaseSerializer):
    """Structural validation only — password strength is enforced by
    PasswordPolicyService in the service layer, since it is config-driven."""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=1)
    confirm_password = serializers.CharField(min_length=1)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class SetPasswordSerializer(WriteMixin, BaseSerializer):
    """Structural validation only — password strength is enforced by
    PasswordPolicyService in the service layer, since it is config-driven."""

    token = serializers.CharField(min_length=1)
    new_password = serializers.CharField(min_length=1)
    confirm_password = serializers.CharField(min_length=1)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class ForceChangePasswordSerializer(WriteMixin, BaseSerializer):
    """Structural validation only — password strength is enforced by
    PasswordPolicyService in the service layer, since it is config-driven."""

    new_password = serializers.CharField(min_length=1)
    confirm_password = serializers.CharField(min_length=1)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class MeSerializer(BaseSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    theme = serializers.ChoiceField(choices=ThemeChoices.choices)
    avatar_url = serializers.CharField(allow_null=True)
    is_sso = serializers.BooleanField()
    sso_provider_name = serializers.CharField(allow_null=True)
