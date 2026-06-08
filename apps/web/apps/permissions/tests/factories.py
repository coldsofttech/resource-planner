from apps.permissions.models import PermissionCategory


def make_permission_category(
    module: str = "projects",
    codename: str = "view",
    name: str = "View",
    order: int = 1,
) -> PermissionCategory:
    return PermissionCategory.objects.create(
        module=module,
        codename=codename,
        name=name,
        label=f"{name} {module.title()}",
        order=order,
    )
