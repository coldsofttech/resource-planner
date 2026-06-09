from apps.employment_types.models import EmploymentType


def make_employment_type(
    name: str = "Full-time",
    is_active: bool = True,
    is_default: bool = False,
    **overrides,
) -> EmploymentType:
    return EmploymentType.objects.create(
        name=name,
        is_active=is_active,
        is_default=is_default,
        **overrides,
    )


def make_csv_file(content: str, name: str = "employment_types.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
