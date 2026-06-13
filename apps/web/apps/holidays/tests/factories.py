import datetime

from apps.holidays.models import Holiday


def make_holiday(
    name: str = "Christmas Day",
    date: datetime.date | None = None,
    location=None,
    **overrides,
) -> Holiday:
    from apps.locations.tests.factories import make_location

    if date is None:
        date = datetime.date(2025, 12, 25)
    if location is None:
        location = make_location()
    return Holiday.objects.create(name=name, date=date, location=location, **overrides)


def make_csv_file(content: str, name: str = "holidays.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
