from django.db import models

from apps.business_units.models import BusinessUnit
from apps.core.models import CodeModel, CreatedAtModel
from apps.products.models import Product

from ..constants import OnboardingStatus
from .onboarding_contact import OnboardingContact
from .project import Project


class Onboarding(CodeModel, CreatedAtModel):
    MODEL_CODE = "PROJONB"

    project_name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True, related_name="onboardings")
    business_units = models.ManyToManyField(
        BusinessUnit,
        blank=True,
        related_name="onboardings",
    )
    requirements = models.TextField(blank=True, default="")
    tentative_start_date = models.DateField(null=True, blank=True)
    tentative_end_date = models.DateField(null=True, blank=True)
    project_code = models.CharField(max_length=50, blank=True, default="")
    risk = models.TextField(blank=True, default="")
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="onboardings",
        db_index=True,
    )
    requester = models.ForeignKey(
        OnboardingContact,
        on_delete=models.PROTECT,
        related_name="onboarding_requests",
        db_index=True,
    )
    accountable_executive = models.ForeignKey(
        OnboardingContact,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="onboarding_accountable",
        db_index=True,
    )
    contacts = models.ManyToManyField(
        OnboardingContact,
        blank=True,
        related_name="onboarding_contacts",
    )
    status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.project_name
