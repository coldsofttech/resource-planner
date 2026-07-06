from django.db import models


class Confidence(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very High"


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very High"


class ProjectEstimateStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    REVIEWED = "REVIEWED", "Reviewed"
    SHARED = "SHARED", "Shared"
    APPROVED = "APPROVED", "Approved"
    SUPERSEDED = "SUPERSEDED", "Superseded"


class ProjectSize(models.TextChoices):
    XS = "XS", "X-Small"
    S = "S", "Small"
    M = "M", "Medium"
    L = "L", "Large"
    XL = "XL", "X-Large"


class ProjectEstimateAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"
    APPROVED = "APPROVED", "Approved"
    SUPERSEDED = "SUPERSEDED", "Superseded"


class ProjectBudgetAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"


class ContactRole(models.TextChoices):
    PROJECT = "project", "Project"
    FINANCE = "finance", "Finance"


class ActualsRiskType(models.TextChoices):
    WARNING = "warning", "Warning"
    AT_RISK = "at_risk", "At Risk"


class OnboardingContactRole(models.TextChoices):
    REQUESTER = "requester", "Requester"
    ACCOUNTABLE_EXECUTIVE = "accountable_executive", "Accountable Executive"
    POINT_OF_CONTACT = "point_of_contact", "Point of Contact"


class OnboardingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
