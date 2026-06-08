from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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
    first_name = serializers.CharField(min_length=1, max_length=150)
    last_name = serializers.CharField(min_length=1, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=12)
    confirm_password = serializers.CharField(min_length=12)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


class ForgotPasswordResetSerializer(WriteMixin, BaseSerializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=12)
    confirm_password = serializers.CharField(min_length=12)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

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
