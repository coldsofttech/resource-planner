from apps.roles.models import Role


def make_role(
    role: str = "Developer",
    is_active: bool = True,
    is_default: bool = False,
    is_assignable: bool = False,
    is_leadership: bool = False,
    **overrides,
) -> Role:
    return Role.objects.create(
        role=role,
        is_active=is_active,
        is_default=is_default,
        is_assignable=is_assignable,
        is_leadership=is_leadership,
        **overrides,
    )


def make_csv_file(content: str, name: str = "roles.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
