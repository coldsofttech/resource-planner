class VersionCodeConverter:
    """Matches version path segments like "v1", "v12" and converts to/from int."""

    regex = r"v\d+"

    def to_python(self, value: str) -> int:
        return int(value[1:])

    def to_url(self, value: int) -> str:
        return f"v{value}"
