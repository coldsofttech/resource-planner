from apps.business_units.models import BusinessUnit


def make_business_unit(
    name: str = "Finance",
    short_name: str = "FIN",
    is_active: bool = True,
) -> BusinessUnit:
    return BusinessUnit.objects.create(
        name=name,
        short_name=short_name,
        is_active=is_active,
    )


def make_csv_file(content: str, name: str = "business_units.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
