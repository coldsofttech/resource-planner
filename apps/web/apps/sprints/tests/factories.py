from datetime import date

from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.constants import SprintStatus
from apps.sprints.models import Capacity, Sprint
from apps.users.models import User


def make_sprint(
    financial_year=None,
    sprint_number: int = 1,
    name: str = "Sprint 1",
    start_date: date = date(2024, 4, 1),
    end_date: date = date(2024, 4, 14),
    status: str = SprintStatus.FUTURE,
    is_active: bool = True,
    is_overridden: bool = False,
    is_closed: bool = False,
    note: str = "",
    **overrides,
) -> Sprint:
    if financial_year is None:
        financial_year = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
        )
    return Sprint.objects.create(
        financial_year=financial_year,
        sprint_number=sprint_number,
        name=name,
        start_date=start_date,
        end_date=end_date,
        status=status,
        is_active=is_active,
        is_overridden=is_overridden,
        is_closed=is_closed,
        note=note,
        **overrides,
    )


def make_capacity(
    sprint: Sprint,
    member: User,
    working_days=10,
    holiday_days=0,
    leave_days=0,
    net_capacity=10,
    **overrides,
) -> Capacity:
    return Capacity.objects.create(
        sprint=sprint,
        member=member,
        working_days=working_days,
        holiday_days=holiday_days,
        leave_days=leave_days,
        net_capacity=net_capacity,
        **overrides,
    )


class FakeCsvFile:
    """Lightweight file-like object for import tests."""

    def __init__(self, content: str, name: str = "sprints.csv") -> None:
        self.name = name
        self._data = content.encode("utf-8")
        self.size = len(self._data)

    def read(self) -> bytes:
        return self._data
