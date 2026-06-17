import logging
import os

from django.db import transaction

from apps.core.services import (
    ExportService,
    FilterableQueryService,
    ImportService,
)

logger = logging.getLogger(__name__)


class GroupsAdminService(FilterableQueryService):
    """Admin-facing group management (create, activate, deactivate, delete, members)."""

    _MODULE = "users"
    _RESOURCE_TYPE = "group"

    filterable_fields: dict[str, str] = {
        "is_admin_group": "is_admin_group",
        "is_system": "is_system",
    }
    search_fields: list[str] = ["group__name", "description"]
    sortable_fields: list[str] = ["group__name", "created_at"]
    default_ordering: list[str] = ["group__name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        from apps.users.selectors import get_all_groups

        return get_all_groups()

    def apply_filters(self, qs, filters: dict):
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(is_active=False)
        elif str(is_active_raw).lower() in ("true", "1"):
            qs = qs.filter(is_active=True)
        return super().apply_filters(qs, filters)

    def get(self, code: str):
        from apps.core.exceptions import NotFoundException
        from apps.users.selectors import get_group_by_code

        obj = get_group_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Group", lookup_field="code", lookup_value=code
            )
        return obj

    def stats(self) -> dict:
        from django.db.models import Count, Q

        from apps.users.models import GroupProfile

        qs = GroupProfile.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
            inactive=Count("id", filter=Q(is_active=False)),
            admin_groups=Count("id", filter=Q(is_admin_group=True)),
        )
        return {
            "total": qs["total"],
            "active": qs["active"],
            "inactive": qs["inactive"],
            "admin_groups": qs["admin_groups"],
        }

    @transaction.atomic
    def create(self, *, name: str, description: str = ""):
        from apps.core.exceptions import AlreadyExistsException
        from apps.users.models import Group, GroupProfile

        if Group.objects.filter(name=name).exists():
            raise AlreadyExistsException(
                detail="A group with this name already exists."
            )

        group = Group.objects.create(name=name)
        profile = GroupProfile.objects.create(
            group=group,
            description=description,
            created_by=self.user,
            updated_by=self.user,
        )
        return profile

    @transaction.atomic
    def update(self, code: str, **data):
        from apps.core.exceptions import AlreadyExistsException
        from apps.users.models import Group

        profile = self.get(code)
        name = data.get("name")
        if name and name != profile.group.name:
            if Group.objects.filter(name=name).exclude(pk=profile.group.pk).exists():
                raise AlreadyExistsException(
                    detail="A group with this name already exists."
                )
            profile.group.name = name
            profile.group.save(update_fields=["name"])

        if "description" in data:
            profile.description = data["description"]

        profile.updated_by = self.user
        profile.save(update_fields=["description", "updated_by", "updated_at"])
        return self.get(code)

    @transaction.atomic
    def activate(self, code: str):
        profile = self.get(code)
        profile.is_active = True
        profile.updated_by = self.user
        profile.save(update_fields=["is_active", "updated_by", "updated_at"])
        logger.info("Group %s activated by %s.", code, self.user)
        return self.get(code)

    @transaction.atomic
    def deactivate(self, code: str):
        profile = self.get(code)
        profile.is_active = False
        profile.updated_by = self.user
        profile.save(update_fields=["is_active", "updated_by", "updated_at"])
        logger.info("Group %s deactivated by %s.", code, self.user)
        return self.get(code)

    @transaction.atomic
    def delete(self, code: str) -> None:
        profile = self.get(code)
        group = profile.group
        group.delete()
        logger.info("Group %s permanently deleted by %s.", code, self.user)

    def list_members(self, code: str, params):
        from django.db.models import Q

        from apps.core.services import paginate_queryset
        from apps.users.selectors import get_group_members

        self.get(code)  # raises NotFoundException if not found
        qs = get_group_members(code)

        filters = params.filters or {}
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(user__is_active=False)
        else:
            qs = qs.filter(user__is_active=True)

        search = (params.search or "").strip()
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(user__email__icontains=search)
                | Q(display_name__icontains=search)
            )

        return paginate_queryset(qs, params.page, params.page_size)

    @transaction.atomic
    def assign_member(self, code: str, member_code: str) -> None:
        from apps.core.exceptions import AlreadyExistsException, NotFoundException
        from apps.users.models import UserProfile

        profile = self.get(code)
        try:
            member = UserProfile.objects.select_related("user").get(code=member_code)
        except UserProfile.DoesNotExist as exc:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            ) from exc

        if member.user.groups.filter(pk=profile.group.pk).exists():
            raise AlreadyExistsException(detail="Member is already in this group.")

        profile.group.user_set.add(member.user)
        logger.info(
            "Member %s assigned to group %s by %s.", member_code, code, self.user
        )

    @transaction.atomic
    def unassign_member(self, code: str, member_code: str) -> None:
        from apps.core.exceptions import NotFoundException
        from apps.users.models import UserProfile

        profile = self.get(code)
        try:
            member = UserProfile.objects.select_related("user").get(code=member_code)
        except UserProfile.DoesNotExist as exc:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            ) from exc

        profile.group.user_set.remove(member.user)
        logger.info(
            "Member %s removed from group %s by %s.", member_code, code, self.user
        )


class GroupsExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "name": "Name",
        "code": "Code",
        "description": "Description",
        "is_admin_group": "Admin Group",
        "is_active": "Active",
        "member_count": "Member Count",
        "created_at": "Created On",
        "created_by": "Created By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "name",
        "code",
        "description",
        "is_admin_group",
        "is_active",
        "member_count",
    ]
    EXPORT_FILENAME = "groups_export"
    EXPORT_MODULE_NAME = "Groups"

    def _get_field_value(self, obj, field: str) -> str:
        if field == "name":
            return obj.group.name
        if field == "is_active":
            return "Yes" if obj.is_active else "No"
        if field == "is_admin_group":
            return "Yes" if obj.is_admin_group else "No"
        if field == "member_count":
            return str(getattr(obj, "member_count", 0) or 0)
        return super()._get_field_value(obj, field)

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ):
        from apps.core.exceptions import ValidationException
        from apps.users.selectors import get_all_groups

        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = get_all_groups()
        if filters:
            is_active_raw = filters.get("is_active")
            if str(is_active_raw or "").lower() == "all":
                pass
            elif str(is_active_raw or "").lower() in ("false", "0"):
                qs = qs.filter(is_active=False)
            elif str(is_active_raw or "").lower() in ("true", "1"):
                qs = qs.filter(is_active=True)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(group__name__icontains=search) | Q(description__icontains=search)
                )

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        allowed = "csv, xlsx, pdf, json"
        raise ValidationException(
            f"Unsupported export format '{export_format}'. Allowed: {allowed}."
        )


class GroupsImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1_000
    MAX_IMPORT_FILE_SIZE_MB = 5

    def validate_file(self, file) -> None:
        from apps.core.exceptions import ValidationException

        _, ext = os.path.splitext(file.name)
        if ext.lower().lstrip(".") not in self.SUPPORTED_IMPORT_FORMATS:
            raise ValidationException(
                "Unsupported file format. Allowed: "
                f"{', '.join(self.SUPPORTED_IMPORT_FORMATS)}."
            )
        file_size_mb = file.size / (1024 * 1024)
        if file_size_mb > self.MAX_IMPORT_FILE_SIZE_MB:
            raise ValidationException(
                "File too large. Maximum allowed size: "
                f"{self.MAX_IMPORT_FILE_SIZE_MB} MB."
            )

    def validate_row(self, row: dict, row_num: int) -> list[dict]:
        errors: list[dict] = []
        name = (row.get("name") or "").strip()
        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 150:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 150 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        import csv
        import io

        from apps.core.exceptions import ValidationException
        from apps.users.models import Group

        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name"}
        actual_columns = set(reader.fieldnames or [])
        missing = required_columns - actual_columns
        if missing:
            raise ValidationException(
                f"Missing required column(s): {', '.join(sorted(missing))}."
            )

        rows = list(reader)
        if len(rows) > self.MAX_IMPORT_ROWS:
            raise ValidationException(
                f"Too many rows. Maximum allowed: {self.MAX_IMPORT_ROWS}."
            )

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        group_svc = GroupsAdminService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            description = (row.get("description") or "").strip()

            if Group.objects.filter(name=name).exists():
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A group named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                group_svc.create(name=name, description=description)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }
