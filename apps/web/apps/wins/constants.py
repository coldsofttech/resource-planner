from django.db import models


class WinStatus(models.TextChoices):
    OPEN = "open", "Open"
    REVIEW_COMPLETE = "review_complete", "Review Complete"
    CLOSED = "closed", "Closed"


class MonthlyWinStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PHASE_1_OPEN = "phase_1_open", "Phase 1 Open"
    PHASE_1_CLOSED = "phase_1_closed", "Phase 1 Closed"
    PHASE_2_OPEN = "phase_2_open", "Phase 2 Open"
    PHASE_2_CLOSED = "phase_2_closed", "Phase 2 Closed"
    WINS_DECLARED = "wins_declared", "Wins Declared"


class SurveyPhase(models.TextChoices):
    PHASE_1 = "phase_1", "Phase 1"
    PHASE_2 = "phase_2", "Phase 2"


class SurveyStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    OVERRIDDEN = "overridden", "Overridden"


class WinCategory(models.TextChoices):
    DELIVERY = "delivery", "Delivery"
    OPERATIONAL_EXCELLENCE = "operational_excellence", "Operational Excellence"
