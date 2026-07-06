import logging

from django.db import transaction

from apps.core.services import ExportService, FilterableQueryService
from apps.users.models import UserProfile

logger = logging.getLogger(__name__)


class MembersService(FilterableQueryService):
    """Manages workforce details for all members (admin-facing)."""

    _MODULE = "users"
    _RESOURCE_TYPE = "member"

    filterable_fields: dict[str, str] = {
        "role": "role__code",
        "employment_type": "employment_type__code",
        "location": "location__code",
        "team": "user__team_assignments__team__code",
        "skill": "skills__code",
    }
    search_fields: list[str] = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "display_name",
    ]
    sortable_fields: list[str] = [
        "user__last_name",
        "user__first_name",
        "user__email",
        "joined_date",
        "display_name",
        "email",
    ]
    _sort_field_map: dict[str, str] = {
        "email": "user__email",
    }
    default_ordering: list[str] = ["user__last_name", "user__first_name"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        from apps.users.selectors import get_all_members

        return get_all_members()

    def apply_filters(self, qs, filters: dict):
        is_active_raw = filters.get("is_active", "")
        if str(is_active_raw).lower() == "all":
            pass
        elif str(is_active_raw).lower() in ("false", "0"):
            qs = qs.filter(user__is_active=False)
        else:
            qs = qs.filter(user__is_active=True)
        qs = super().apply_filters(qs, filters)
        if filters.get("team") or filters.get("skill"):
            qs = qs.distinct()
        return qs

    def apply_ordering(self, qs, sorts):
        from apps.core.types import SortParam

        order_fields = []
        for s in sorts:
            if not isinstance(s, SortParam) or s.sort_by not in self.sortable_fields:
                continue
            field = self._sort_field_map.get(s.sort_by, s.sort_by)
            order_fields.append(f"-{field}" if s.direction == "desc" else field)
        return qs.order_by(*(order_fields or self.default_ordering))

    def get(self, code: str) -> UserProfile:
        from apps.core.exceptions import NotFoundException
        from apps.users.selectors import get_member_by_code

        obj = get_member_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs: object) -> UserProfile:
        from apps.core.exceptions import ValidationException

        profile = self.get(code)

        profile.updated_by = self.user
        update_fields = ["updated_at", "updated_by"]

        if "location" in kwargs:
            loc_code = kwargs.pop("location")
            if loc_code:
                from apps.locations.models import Location

                try:
                    profile.location = Location.objects.get(
                        code=loc_code, is_active=True
                    )
                except Location.DoesNotExist as exc:
                    raise ValidationException(
                        f"Location '{loc_code}' not found."
                    ) from exc
            else:
                profile.location = None
            update_fields.append("location")

        if "employment_type" in kwargs:
            et_code = kwargs.pop("employment_type")
            if et_code:
                from apps.employment_types.models import EmploymentType

                try:
                    profile.employment_type = EmploymentType.objects.get(
                        code=et_code, is_active=True
                    )
                except EmploymentType.DoesNotExist as exc:
                    raise ValidationException(
                        f"Employment type '{et_code}' not found."
                    ) from exc
            else:
                profile.employment_type = None
            update_fields.append("employment_type")

        if "role" in kwargs:
            role_code = kwargs.pop("role")
            if role_code:
                from apps.roles.models import Role

                try:
                    profile.role = Role.objects.get(code=role_code, is_active=True)
                except Role.DoesNotExist as exc:
                    raise ValidationException(f"Role '{role_code}' not found.") from exc
            else:
                profile.role = None
            update_fields.append("role")

        for field in ("joined_date", "leaving_date", "default_holidays"):
            if field in kwargs:
                setattr(profile, field, kwargs.pop(field))
                update_fields.append(field)

        profile.save(update_fields=update_fields)
        return profile


class MembersExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "first_name": "First Name",
        "last_name": "Last Name",
        "display_name": "Display Name",
        "email": "Email",
        "is_active": "Active",
        "location": "Location",
        "employment_type": "Employment Type",
        "role": "Role",
        "joined_date": "Joined Date",
        "leaving_date": "Leaving Date",
        "default_holidays": "Default Holidays",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "first_name",
        "last_name",
        "display_name",
        "email",
        "is_active",
        "location",
        "employment_type",
        "role",
        "joined_date",
    ]
    EXPORT_FILENAME = "members_export"
    EXPORT_MODULE_NAME = "Members"

    def _get_field_value(self, obj: UserProfile, field: str) -> str:
        if field in ("first_name", "last_name", "email"):
            return str(getattr(obj.user, field, "") or "")
        if field == "is_active":
            return "Yes" if obj.user.is_active else "No"
        if field == "location":
            if obj.location:
                return f"{obj.location.city}, {obj.location.country}"
            return ""
        if field == "employment_type":
            return obj.employment_type.name if obj.employment_type else ""
        if field == "role":
            return obj.role.role if obj.role else ""
        return super()._get_field_value(obj, field)

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ):
        from apps.core.exceptions import ValidationException
        from apps.users.selectors import get_all_members

        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = get_all_members()
        if filters:
            is_active_raw = filters.get("is_active")
            if str(is_active_raw or "").lower() == "all":
                pass
            elif str(is_active_raw or "").lower() in ("false", "0"):
                qs = qs.filter(user__is_active=False)
            else:
                qs = qs.filter(user__is_active=True)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(user__first_name__icontains=search)
                    | Q(user__last_name__icontains=search)
                    | Q(user__email__icontains=search)
                    | Q(display_name__icontains=search)
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
