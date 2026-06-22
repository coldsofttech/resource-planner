from django.db.models import QuerySet

from apps.contacts.models import Contact
from apps.projects.models import Project, ProjectContact


def get_all_project_contacts(project: Project) -> QuerySet[ProjectContact]:
    return (
        ProjectContact.objects.select_related("contact", "created_by", "updated_by")
        .filter(project=project)
        .order_by("contact__name")
    )


def get_project_contact_by_code(code: str) -> ProjectContact | None:
    try:
        return ProjectContact.objects.select_related(
            "project", "contact", "created_by", "updated_by"
        ).get(code=code)
    except ProjectContact.DoesNotExist:
        return None


def project_contact_exists(
    project: Project,
    contact: Contact,
    exclude_pk: int | None = None,
) -> bool:
    qs = ProjectContact.objects.filter(project=project, contact=contact)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_contact_by_name_and_email(name: str, email: str) -> Contact | None:
    try:
        return Contact.objects.get(
            name__iexact=name.strip(), email__iexact=email.strip()
        )
    except Contact.DoesNotExist:
        return None
