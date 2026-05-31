import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

AWS_ACCESS_KEY_ID_VALIDATOR = RegexValidator(
    regex=r"^[A-Z0-9]{20}$",
    message="Enter a valid AWS Access Key ID (20 uppercase alphanumeric characters).",
    code="invalid_aws_access_key_id",
)

AWS_SECRET_ACCESS_KEY_VALIDATOR = RegexValidator(
    regex=r"^[A-Za-z0-9/+=]{40}$",
    message="Enter a valid AWS Secret Access Key (40 characters).",
    code="invalid_aws_secret_access_key",
)

AWS_REGION_VALIDATOR = RegexValidator(
    regex=r"^[a-z]{2}-[a-z]+-\d+$",
    message="Enter a valid AWS region (e.g. eu-west-1, us-east-1, ap-southeast-2).",
    code="invalid_aws_region",
)

S3_ARN_VALIDATOR = RegexValidator(
    regex=r"^arn:aws:s3:::[a-z0-9][a-z0-9.\-]{1,61}[a-z0-9]$",
    message="Enter a valid S3 bucket ARN (e.g. arn:aws:s3:::my-bucket).",
    code="invalid_s3_arn",
)


def validate_x509_cert(value: str) -> None:
    """
    Validates a bare X.509 certificate body
    (no -----BEGIN/END CERTIFICATE----- markers).
    """
    if not value:
        return
    stripped = re.sub(r"[\s\r\n]", "", value)
    if "-----" in stripped:
        raise ValidationError(
            (
                "Do not include the -----BEGIN CERTIFICATE----- header or footer — "
                "paste only the base64 body."
            ),
            code="invalid_x509_cert",
        )
    if len(stripped) < 50 or not re.fullmatch(r"[A-Za-z0-9+/]+=*", stripped):
        raise ValidationError(
            "Enter a valid base64-encoded X.509 certificate body.",
            code="invalid_x509_cert",
        )
