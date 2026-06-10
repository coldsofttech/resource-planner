from datetime import date

from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear


def make_financial_year(
    start_date: date = date(2024, 4, 1),
    end_date: date = date(2025, 3, 31),
    status: str = FinancialYearStatus.FUTURE,
    is_active: bool = True,
    note: str = "",
    **overrides,
) -> FinancialYear:
    return FinancialYear.objects.create(
        start_date=start_date,
        end_date=end_date,
        status=status,
        is_active=is_active,
        note=note,
        **overrides,
    )


class FakeCsvFile:
    """Lightweight file-like object for import tests."""

    def __init__(self, content: str, name: str = "financial_years.csv") -> None:
        self.name = name
        self._data = content.encode("utf-8")
        self.size = len(self._data)

    def read(self) -> bytes:
        return self._data
