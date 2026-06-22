from django.core.validators import RegexValidator

RECHARGE_TYPE_VALIDATOR = RegexValidator(
    regex=r"^[A-Z][A-Z0-9_]*$",
    message="Name must be UPPER_SNAKE_CASE (e.g. PROJECT, BAU, HOLIDAY).",
    code="invalid_name",
)
