from apps.tags.models import Tag


def make_tag(name: str = "backend", **overrides) -> Tag:
    return Tag.objects.create(name=name, **overrides)
