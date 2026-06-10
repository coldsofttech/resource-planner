from django.db import models


class HalfDayPeriod(models.TextChoices):
    MORNING = "AM", "Morning (AM)"
    AFTERNOON = "PM", "Afternoon (PM)"
