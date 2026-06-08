from apps.locations.models import Location


def make_location(
    city: str = "London",
    country: str = "United Kingdom",
    is_active: bool = True,
    is_default: bool = False,
) -> Location:
    return Location.objects.create(
        city=city,
        country=country,
        is_active=is_active,
        is_default=is_default,
    )


def make_csv_file(content: str, name: str = "locations.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
