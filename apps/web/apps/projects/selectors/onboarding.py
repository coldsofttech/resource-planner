from __future__ import annotations

from django.db.models import Prefetch, QuerySet

from apps.projects.constants import OnboardingStatus
from apps.projects.models import Onboarding, OnboardingAttachment, OnboardingContact
from apps.teams.models import Team

# Only surface attachments that were fully stored (have a non-empty file_path).
# Records with file_path="" are pre-migration artifacts created before the file
# upload system existed — they carry a filename but no actual file content.
_stored_attachments = Prefetch(
    "attachments",
    queryset=OnboardingAttachment.objects.exclude(file_path="").order_by("file_name"),
)


def get_all_onboardings(
    *,
    status: str | None = None,
    search: str = "",
) -> QuerySet[Onboarding]:
    from django.db.models import Q

    qs = Onboarding.objects.select_related(
        "project",
        "requester",
        "accountable_executive",
    ).prefetch_related(
        "products", "business_units", "contacts", "links", _stored_attachments
    )

    if status:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(
            Q(project_name__icontains=search)
            | Q(requester__email__icontains=search)
            | Q(code__icontains=search)
        )

    return qs.order_by("-created_at")


def get_onboarding_by_code(code: str) -> Onboarding | None:
    return (
        Onboarding.objects.select_related(
            "project",
            "requester",
            "accountable_executive",
        )
        .prefetch_related(
            "products", "business_units", "contacts", "links", _stored_attachments
        )
        .filter(code=code)
        .first()
    )


def get_onboarding_contact_by_email(email: str) -> OnboardingContact | None:
    return OnboardingContact.objects.filter(email=email).first()


def get_onboarding_attachment_by_code(code: str) -> OnboardingAttachment | None:
    return (
        OnboardingAttachment.objects.select_related("onboarding")
        .filter(code=code)
        .first()
    )


def get_attachments_for_onboarding(
    onboarding: Onboarding,
) -> QuerySet[OnboardingAttachment]:
    return (
        OnboardingAttachment.objects.filter(onboarding=onboarding)
        .exclude(file_path="")
        .order_by("file_name")
    )


def onboarding_attachment_filename_exists(
    onboarding: Onboarding, file_name: str
) -> bool:
    return (
        OnboardingAttachment.objects.filter(onboarding=onboarding, file_name=file_name)
        .exclude(file_path="")
        .exists()
    )


def get_onboarding_stats() -> dict:
    pending = Onboarding.objects.filter(status=OnboardingStatus.PENDING).count()
    accepted = Onboarding.objects.filter(status=OnboardingStatus.ACCEPTED).count()
    teams = Team.objects.filter(is_active=True).count()
    return {"pending": pending, "approved": accepted, "teams": teams}
