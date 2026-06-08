from apps.audit.models import Audit


def make_audit(
    module: str = "projects",
    resource_type: str = "project",
    resource_code: str = "PROJ-1",
    action: str = "create",
    **kwargs,
) -> Audit:
    return Audit.objects.create(
        module=module,
        resource_type=resource_type,
        resource_code=resource_code,
        action=action,
        **kwargs,
    )
