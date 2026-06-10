from django.db import models

from apps.core.models import ActivatableModel, AuditableModel, CodeModel
from apps.financial_years.constants import FinancialYearStatus


class FinancialYear(CodeModel, AuditableModel, ActivatableModel):
    MODEL_CODE = "FY"

    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    long_fy = models.CharField(max_length=20, editable=False, db_index=True)
    short_fy = models.CharField(max_length=10, editable=False)
    span_days = models.PositiveIntegerField(editable=False, default=0)
    status = models.CharField(
        max_length=20,
        choices=FinancialYearStatus.CHOICES,
        default=FinancialYearStatus.FUTURE,
        db_index=True,
    )
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-start_date"]
        permissions = [
            ("import_financialyear", "Can import financial years"),
            ("export_financialyear", "Can export financial years"),
        ]

    def __str__(self) -> str:
        return self.long_fy

    def save(self, *args, **kwargs) -> None:
        if self.start_date and self.end_date:
            sy, ey = self.start_date.year, self.end_date.year
            self.long_fy = f"FY{sy}-{ey}"
            self.short_fy = f"FY{str(sy)[2:]}-{str(ey)[2:]}"
            self.span_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)
