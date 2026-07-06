from __future__ import annotations

import logging

from django.db import transaction

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.utils import build_email_sender
from apps.projects import selectors
from apps.projects.constants import OnboardingContactRole, OnboardingStatus
from apps.projects.models import (
    Onboarding,
    OnboardingContact,
    OnboardingLink,
    ProjectLink,
)

logger = logging.getLogger(__name__)


def _get_or_create_contact(email: str, role: str) -> OnboardingContact:
    obj = selectors.get_onboarding_contact_by_email(email)
    if obj is None:
        obj = OnboardingContact.objects.create(email=email, role=role)
    return obj


def _send_confirmation_email(onboarding: Onboarding) -> None:
    try:
        sender = build_email_sender()
        requester_name = onboarding.requester.name or onboarding.requester.email
        subject = f"Demand request received: {onboarding.project_name}"
        body = (
            f"Hi {requester_name},\n\n"
            f"Thank you for submitting your demand request.\n\n"
            f"Project Name: {onboarding.project_name}\n"
            f"Reference: {onboarding.code}\n\n"
            f"Our team will review your request and get back to you shortly.\n\n"
            f"Regards,\nResource Planner Team"
        )
        sender.send(to=onboarding.requester.email, subject=subject, body=body)
    except Exception:
        logger.warning("Failed to send onboarding confirmation email.")


class OnboardingService:
    @transaction.atomic
    def submit(
        self,
        *,
        project_name: str,
        requester_email: str,
        requirements: str = "",
        risk: str = "",
        project_code: str = "",
        tentative_start_date=None,
        tentative_end_date=None,
        product_codes: list[str] | None = None,
        business_unit_codes: list[str] | None = None,
        accountable_executive_email: str | None = None,
        contact_emails: list[str] | None = None,
        links: list[dict] | None = None,
    ) -> Onboarding:
        from apps.business_units.models import BusinessUnit
        from apps.products.models import Product

        requester = _get_or_create_contact(
            requester_email,
            OnboardingContactRole.REQUESTER,  # type: ignore[arg-type]
        )

        business_units: list = []
        if business_unit_codes:
            business_units = list(
                BusinessUnit.objects.filter(code__in=business_unit_codes)
            )

        accountable_executive = None
        if accountable_executive_email:
            accountable_executive = _get_or_create_contact(
                accountable_executive_email,
                OnboardingContactRole.ACCOUNTABLE_EXECUTIVE,  # type: ignore[arg-type]
            )

        obj = Onboarding.objects.create(
            project_name=project_name,
            requester=requester,
            accountable_executive=accountable_executive,
            requirements=requirements,
            risk=risk,
            project_code=project_code,
            tentative_start_date=tentative_start_date,
            tentative_end_date=tentative_end_date,
            status=OnboardingStatus.PENDING,
        )

        if product_codes:
            products = list(Product.objects.filter(code__in=product_codes))
            obj.products.set(products)

        if business_units:
            obj.business_units.set(business_units)

        contact_objs: list[OnboardingContact] = []
        for email in contact_emails or []:
            if email and email != requester_email:
                contact = _get_or_create_contact(
                    email,
                    OnboardingContactRole.POINT_OF_CONTACT,  # type: ignore[arg-type]
                )
                contact_objs.append(contact)
        if contact_objs:
            obj.contacts.set(contact_objs)

        for link_data in links or []:
            url = link_data.get("url", "").strip()
            if url:
                OnboardingLink.objects.create(
                    onboarding=obj,
                    url=url,
                    title=link_data.get("title", ""),
                )

        _send_confirmation_email(obj)
        return obj

    def get(self, code: str) -> Onboarding:
        obj = selectors.get_onboarding_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Onboarding", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, params=None):
        from apps.core.services import paginate_queryset
        from apps.core.types import ListParams

        if params is None:
            params = ListParams()

        status = params.filters.get("status") or None
        qs = selectors.get_all_onboardings(status=status, search=params.search)
        return paginate_queryset(qs, page=params.page, page_size=params.page_size)

    def stats(self) -> dict:
        return selectors.get_onboarding_stats()


class OnboardingReviewService:
    def __init__(self, *, user) -> None:
        self.user = user

    def _get(self, code: str) -> Onboarding:
        obj = selectors.get_onboarding_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Onboarding", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def accept(self, code: str) -> Onboarding:
        from apps.projects.models import ProjectStatus, ProjectType
        from apps.projects.services.project import ProjectService

        obj = self._get(code)
        if obj.status != OnboardingStatus.PENDING:
            raise ValidationException(
                detail=f"Cannot accept an onboarding with status '{obj.status}'."
            )

        project_type = ProjectType.objects.filter(is_active=True).first()
        project_status = ProjectStatus.objects.filter(is_active=True).first()

        if project_type is None or project_status is None:
            raise ValidationException(
                detail="No active project type or status available to create a project."
            )

        svc = ProjectService(user=self.user)
        project = svc.create(
            name=obj.project_name,
            project_type_code=project_type.code,
            status_code=project_status.code,
        )

        for onboarding_link in obj.links.all():
            ProjectLink.objects.create(
                project=project,
                title=onboarding_link.title or onboarding_link.url[:200],
                url=onboarding_link.url,
                created_by=self.user,
                updated_by=self.user,
            )

        obj.project = project
        obj.status = OnboardingStatus.ACCEPTED
        obj.save(update_fields=["project", "status"])
        return obj

    @transaction.atomic
    def reject(self, code: str) -> Onboarding:
        obj = self._get(code)
        if obj.status != OnboardingStatus.PENDING:
            raise ValidationException(
                detail=f"Cannot reject an onboarding with status '{obj.status}'."
            )
        obj.status = OnboardingStatus.REJECTED
        obj.save(update_fields=["status"])
        return obj
