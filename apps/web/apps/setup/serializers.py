from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from rest_framework import serializers

from apps.core.serializers import BaseSerializer, ReadMixin, WriteMixin


class AdminInputSerializer(WriteMixin, BaseSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        django_validate_password(value)
        return value


class AppInputSerializer(WriteMixin, BaseSerializer):
    app_name = serializers.CharField(max_length=50)
    app_url = serializers.URLField(max_length=100)


class InfrastructureInputSerializer(WriteMixin, BaseSerializer):
    deployment_type = serializers.ChoiceField(choices=["local", "aws"])

    # Local
    fernet_key = serializers.CharField(required=False, write_only=True)

    # AWS
    aws_region = serializers.CharField(required=False)
    secrets_prefix = serializers.CharField(required=False)
    aws_auth_mode = serializers.ChoiceField(choices=["role", "user"], required=False)
    aws_access_key_id = serializers.CharField(required=False, write_only=True)
    aws_secret_access_key = serializers.CharField(required=False, write_only=True)

    def validate_fernet_key(self, value):
        if not value:
            return value
        try:
            from cryptography.fernet import Fernet

            Fernet(value.encode())
        except Exception:
            raise serializers.ValidationError(
                "Invalid Fernet key. "
                "Generate one or paste a valid 32-byte URL-safe base64 key."
            ) from None
        return value

    def validate(self, attrs):
        deployment_type = attrs.get("deployment_type")

        if deployment_type == "local":
            self.validate_required_fields(attrs, ["fernet_key"])

        elif deployment_type == "aws":
            self.validate_required_fields(
                attrs, ["aws_region", "secrets_prefix", "aws_auth_mode"]
            )

            if attrs.get("aws_auth_mode") == "user":
                self.validate_required_fields(
                    attrs, ["aws_access_key_id", "aws_secret_access_key"]
                )

        return attrs


class DatabaseInputSerializer(WriteMixin, BaseSerializer):
    engine = serializers.ChoiceField(choices=["sqlite", "postgresql"])

    host = serializers.CharField(required=False)
    port = serializers.CharField(required=False)
    db_name = serializers.CharField(required=False)
    user_name = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        if attrs.get("engine") == "postgresql":
            self.validate_required_fields(
                attrs, ["host", "port", "db_name", "user_name", "password"]
            )
        return attrs


class StorageInputSerializer(WriteMixin, BaseSerializer):
    storage_type = serializers.ChoiceField(choices=["database", "filesystem", "s3"])

    # File System & S3
    storage_path = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs.get("storage_type") in ("filesystem", "s3"):
            self.validate_required_fields(attrs, ["storage_path"])
        return attrs


class AuthenticationInputSerializer(WriteMixin, BaseSerializer):
    auth_type = serializers.ChoiceField(choices=["classic", "saml", "oauth"])

    # Classic
    self_register = serializers.BooleanField(required=False)

    # OAuth & SAML
    provider_name = serializers.CharField(required=False)

    # OAuth
    client_id = serializers.CharField(required=False)
    client_secret = serializers.CharField(required=False, write_only=True)
    auth_endpoint = serializers.URLField(required=False)
    token_endpoint = serializers.URLField(required=False)
    userinfo_endpoint = serializers.URLField(required=False)
    scope = serializers.CharField(required=False)

    # SAML
    idp_entity_id = serializers.URLField(required=False)
    idp_sso_url = serializers.URLField(required=False)
    idp_x509_cert = serializers.CharField(required=False)
    sp_entity_id = serializers.URLField(required=False, allow_blank=True)
    sp_assertion_url = serializers.URLField(required=False)

    def validate(self, attrs):
        auth_type = attrs.get("auth_type")
        if auth_type == "classic":
            self.validate_required_fields(
                attrs=attrs,
                required_fields=["self_register"],
            )
        elif auth_type == "saml":
            self.validate_required_fields(
                attrs=attrs,
                required_fields=[
                    "provider_name",
                    "idp_entity_id",
                    "idp_sso_url",
                    "idp_x509_cert",
                    "sp_assertion_url",
                ],
            )
        elif auth_type == "oauth":
            self.validate_required_fields(
                attrs=attrs,
                required_fields=[
                    "provider_name",
                    "client_id",
                    "client_secret",
                    "auth_endpoint",
                    "token_endpoint",
                    "userinfo_endpoint",
                    "scope",
                ],
            )

        return attrs


class LoggingInputSerializer(WriteMixin, BaseSerializer):
    log_destination = serializers.ChoiceField(choices=["local", "s3", "cloudwatch"])
    log_name = serializers.CharField()
    log_path = serializers.CharField(required=False)
    log_rotation = serializers.ChoiceField(
        choices=["none", "daily", "weekly", "monthly", "size"],
        required=False,
        default="none",
    )
    log_rotation_size_mb = serializers.IntegerField(required=False, min_value=1)
    log_cleanup_keep_files = serializers.IntegerField(required=False, min_value=1)
    log_cleanup_keep_days = serializers.IntegerField(required=False, min_value=1)
    log_s3_bucket = serializers.CharField(required=False)

    def validate(self, attrs):
        destination = attrs.get("log_destination")
        rotation = attrs.get("log_rotation", "none")

        if destination == "local":
            self.validate_required_fields(attrs, ["log_path"])

        if destination == "s3":
            self.validate_required_fields(attrs, ["log_s3_bucket"])

        if rotation == "size":
            self.validate_required_fields(attrs, ["log_rotation_size_mb"])

        return attrs


class EmailInputSerializer(WriteMixin, BaseSerializer):
    email_type = serializers.ChoiceField(choices=["console", "smtp"])
    from_address = serializers.EmailField()
    from_name = serializers.CharField()

    # SMTP
    smtp_host = serializers.CharField(required=False)
    smtp_port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    smtp_enc_type = serializers.ChoiceField(
        choices=["none", "starttls", "ssl"], required=False
    )
    smtp_auth_enabled = serializers.BooleanField(required=False, default=False)
    smtp_username = serializers.CharField(required=False)
    smtp_password = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        if attrs.get("email_type") == "smtp":
            self.validate_required_fields(
                attrs, ["smtp_host", "smtp_port", "smtp_enc_type"]
            )
            if attrs.get("smtp_auth_enabled"):
                self.validate_required_fields(attrs, ["smtp_username", "smtp_password"])
        return attrs


class SetupInputSerializer(WriteMixin, BaseSerializer):
    admin = AdminInputSerializer()
    app = AppInputSerializer()
    infra = InfrastructureInputSerializer()
    db = DatabaseInputSerializer()
    auth = AuthenticationInputSerializer()
    storage = StorageInputSerializer()
    email = EmailInputSerializer()
    logging = LoggingInputSerializer()


class EmailTestInputSerializer(WriteMixin, BaseSerializer):
    email_type = serializers.ChoiceField(choices=["console", "smtp"])
    from_address = serializers.EmailField()
    from_name = serializers.CharField(required=False, default="")

    # SMTP
    smtp_host = serializers.CharField(required=False)
    smtp_port = serializers.IntegerField(required=False, min_value=1, max_value=65535)
    smtp_enc_type = serializers.ChoiceField(
        choices=["none", "starttls", "ssl"], required=False
    )
    smtp_auth_enabled = serializers.BooleanField(required=False, default=False)
    smtp_username = serializers.CharField(required=False)
    smtp_password = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        if attrs.get("email_type") == "smtp":
            self.validate_required_fields(
                attrs, ["smtp_host", "smtp_port", "smtp_enc_type"]
            )
            if attrs.get("smtp_auth_enabled"):
                self.validate_required_fields(attrs, ["smtp_username", "smtp_password"])
        return attrs


class DbTestInputSerializer(WriteMixin, BaseSerializer):
    host = serializers.CharField()
    port = serializers.CharField()
    db_name = serializers.CharField()
    user_name = serializers.CharField()
    password = serializers.CharField(write_only=True)


class GenerateKeySerializer(ReadMixin, BaseSerializer):
    key = serializers.CharField(read_only=True)


class SetupStepSerializer(ReadMixin, BaseSerializer):
    key = serializers.CharField(read_only=True)
    label = serializers.CharField(read_only=True)
    done = serializers.BooleanField(read_only=True)


class SetupStatusSerializer(ReadMixin, BaseSerializer):
    status = serializers.CharField(read_only=True)
    current_step = serializers.CharField(read_only=True, allow_null=True)
    steps = SetupStepSerializer(many=True, read_only=True)
    error = serializers.CharField(read_only=True, allow_null=True)


class SetupDefaultsSerializer(ReadMixin, BaseSerializer):
    app_name = serializers.CharField(read_only=True)
    self_register = serializers.BooleanField(read_only=True)
    storage_type = serializers.CharField(read_only=True)
    storage_path = serializers.CharField(read_only=True)
    log_name = serializers.CharField(read_only=True)
    log_path = serializers.CharField(read_only=True)
    log_rotation = serializers.CharField(read_only=True)
    log_rotation_size_mb = serializers.IntegerField(read_only=True)
    log_cleanup_keep_files = serializers.IntegerField(read_only=True)
    log_cleanup_keep_days = serializers.IntegerField(read_only=True)
