import datetime

from apps.leaves.models import Leave
from apps.users.models import User


def make_leave(
    member: User | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    is_half_day: bool = False,
    half_day_period: str | None = None,
    days: str = "1",
    note: str = "",
    **overrides,
) -> Leave:
    from apps.users.tests.factories import make_user

    if member is None:
        member = make_user(email="member@example.com")
    if start_date is None:
        start_date = datetime.date(2025, 1, 6)
    if end_date is None:
        end_date = start_date if is_half_day else datetime.date(2025, 1, 10)

    return Leave.objects.create(
        member=member,
        start_date=start_date,
        end_date=end_date,
        is_half_day=is_half_day,
        half_day_period=half_day_period if is_half_day else None,
        days=days,
        note=note,
        **overrides,
    )


def make_csv_file(content: str, name: str = "leaves.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
