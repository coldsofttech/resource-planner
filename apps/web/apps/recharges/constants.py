from django.db import models


class RechargeType(models.TextChoices):
    FORECAST = "forecast", "Forecast"
    ACTUAL = "actual", "Actual"


class RechargeEmailStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    ERROR = "error", "Error"
