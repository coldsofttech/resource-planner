from apps.skills.models import Skill


def make_skill(
    skill: str = "Python", is_active: bool = True, description: str = ""
) -> Skill:
    return Skill.objects.create(
        skill=skill, is_active=is_active, description=description
    )


def make_csv_file(content: str, name: str = "skills.csv"):
    """Wrap CSV text in a file-like object matching UploadedFile's interface."""

    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
