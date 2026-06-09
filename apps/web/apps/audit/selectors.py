from django.db.models import QuerySet

from apps.audit.models import Audit


def get_audit_entries(
    *,
    module: str | None = None,
    resource_type: str | None = None,
    resource_code: str | None = None,
    action: str | None = None,
) -> QuerySet[Audit]:
    qs = Audit.objects.select_related("actor").all()
    if module:
        qs = qs.filter(module=module)
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    if resource_code:
        qs = qs.filter(resource_code=resource_code)
    if action:
        qs = qs.filter(action=action)
    return qs


def get_audit_entries_for_resource(*, resource_code: str) -> QuerySet[Audit]:
    return Audit.objects.select_related("actor").filter(resource_code=resource_code)


def get_audit_entries_for_module(*, module: str) -> QuerySet[Audit]:
    return Audit.objects.select_related("actor").filter(module=module)


def get_audit_entries_for_actor(*, actor) -> QuerySet[Audit]:
    return Audit.objects.filter(actor=actor)
