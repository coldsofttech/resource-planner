import pytest
from django.core.exceptions import ValidationError

from apps.setup.validators import (
    AWS_ACCESS_KEY_ID_VALIDATOR,
    AWS_REGION_VALIDATOR,
    AWS_SECRET_ACCESS_KEY_VALIDATOR,
    S3_ARN_VALIDATOR,
    validate_x509_cert,
)


class TestValidateX509Cert:
    def test_empty_string_passes(self):
        validate_x509_cert("")

    def test_valid_base64_body_passes(self):
        body = "A" * 100
        validate_x509_cert(body)

    def test_cert_with_pem_header_raises(self):
        cert = "-----BEGIN CERTIFICATE-----\nABCDEFGH\n-----END CERTIFICATE-----"
        with pytest.raises(ValidationError, match="Do not include"):
            validate_x509_cert(cert)

    def test_cert_too_short_raises(self):
        with pytest.raises(ValidationError, match="valid base64-encoded"):
            validate_x509_cert("ABC")

    def test_cert_with_invalid_base64_chars_raises(self):
        body = "!" * 100
        with pytest.raises(ValidationError, match="valid base64-encoded"):
            validate_x509_cert(body)

    def test_cert_with_whitespace_stripped_and_valid_passes(self):
        body = ("A" * 100 + "\n") * 3
        validate_x509_cert(body)

    def test_cert_with_valid_padding_passes(self):
        body = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=="
        validate_x509_cert(body)


class TestAwsAccessKeyIdValidator:
    def test_valid_key_passes(self):
        AWS_ACCESS_KEY_ID_VALIDATOR("AKIAIOSFODNN7EXAMPLE")

    def test_lowercase_raises(self):
        with pytest.raises(ValidationError):
            AWS_ACCESS_KEY_ID_VALIDATOR("akiaiosfodnn7example")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            AWS_ACCESS_KEY_ID_VALIDATOR("AKIAIOSFODNN")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            AWS_ACCESS_KEY_ID_VALIDATOR("AKIAIOSFODNN7EXAMPLEXXX")

    def test_special_chars_raises(self):
        with pytest.raises(ValidationError):
            AWS_ACCESS_KEY_ID_VALIDATOR("AKIA!OSFODNN7EXAMPL")


class TestAwsSecretAccessKeyValidator:
    def test_valid_key_passes(self):
        key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        AWS_SECRET_ACCESS_KEY_VALIDATOR(key)

    def test_too_short_raises(self):
        with pytest.raises(ValidationError):
            AWS_SECRET_ACCESS_KEY_VALIDATOR("short")

    def test_invalid_chars_raises(self):
        key = "!" * 40
        with pytest.raises(ValidationError):
            AWS_SECRET_ACCESS_KEY_VALIDATOR(key)

    def test_valid_alphanumeric_key_passes(self):
        key = "A" * 40
        AWS_SECRET_ACCESS_KEY_VALIDATOR(key)


class TestAwsRegionValidator:
    def test_valid_eu_west_passes(self):
        AWS_REGION_VALIDATOR("eu-west-1")

    def test_valid_us_east_passes(self):
        AWS_REGION_VALIDATOR("us-east-1")

    def test_valid_ap_southeast_passes(self):
        AWS_REGION_VALIDATOR("ap-southeast-2")

    def test_uppercase_raises(self):
        with pytest.raises(ValidationError):
            AWS_REGION_VALIDATOR("EU-WEST-1")

    def test_missing_number_raises(self):
        with pytest.raises(ValidationError):
            AWS_REGION_VALIDATOR("eu-west")

    def test_only_two_parts_raises(self):
        with pytest.raises(ValidationError):
            AWS_REGION_VALIDATOR("east-1")


class TestS3ArnValidator:
    def test_valid_arn_passes(self):
        S3_ARN_VALIDATOR("arn:aws:s3:::my-bucket")

    def test_valid_arn_with_dots_passes(self):
        S3_ARN_VALIDATOR("arn:aws:s3:::my.bucket.name")

    def test_missing_prefix_raises(self):
        with pytest.raises(ValidationError):
            S3_ARN_VALIDATOR("my-bucket")

    def test_uppercase_bucket_raises(self):
        with pytest.raises(ValidationError):
            S3_ARN_VALIDATOR("arn:aws:s3:::MY-BUCKET")

    def test_invalid_service_raises(self):
        with pytest.raises(ValidationError):
            S3_ARN_VALIDATOR("arn:aws:ec2:::my-bucket")

    def test_bucket_name_too_short_raises(self):
        with pytest.raises(ValidationError):
            S3_ARN_VALIDATOR("arn:aws:s3:::a")
