import zoneinfo

from django.db import models


class ThemeChoices(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"
    SYSTEM = "system", "System"


TIMEZONE_CHOICES: list[tuple[str, str]] = sorted(
    [(tz, tz) for tz in zoneinfo.available_timezones()]
)
