from apps.contacts.models import Contact


def make_contact(
    name: str = "Test Contact",
    email: str = "contact@example.com",
    **overrides,
) -> Contact:
    return Contact.objects.create(name=name, email=email, **overrides)
