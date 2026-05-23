from django.core.validators import RegexValidator

CONFIG_CODE_VALIDATOR = RegexValidator(
    regex=r"^[A-Z][A-Z0-9_]*$",
    message=(
        "Code must start with an uppercase letter and contain only "
        "uppercase letters, digits, and underscores (e.g. DEFAULT_HOLIDAYS)."
    ),
    code="invalid_config_code",
)
