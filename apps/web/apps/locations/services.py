from __future__ import annotations

import csv
import io
import os

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import (
    AuditableService,
    ExportService,
    FilterableQueryService,
    ImportService,
)
from apps.locations import selectors
from apps.locations.models import Location


class LocationService(AuditableService, FilterableQueryService):
    _MODULE = "locations"
    _RESOURCE_TYPE = "location"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["city", "country"]
    sortable_fields: list[str] = [
        "city",
        "country",
        "is_active",
        "is_default",
        "created_at",
    ]
    default_ordering: list[str] = ["country", "city"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_locations()

    def _snapshot(self, location: Location) -> dict:
        return {
            "code": location.code,
            "city": location.city,
            "country": location.country,
            "is_active": location.is_active,
            "is_default": location.is_default,
        }

    def get(self, code: str, *args, **kwargs) -> Location:
        obj = selectors.get_location_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Location", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        city: str,
        country: str,
        is_active: bool = True,
        is_default: bool = False,
    ) -> Location:
        if selectors.location_exists(city, country):
            raise AlreadyExistsException(
                detail=f"A location for '{city}, {country}' already exists."
            )
        location = Location.objects.create(
            city=city,
            country=country,
            is_active=is_active,
            is_default=is_default,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=location.code,
            after=self._snapshot(location),
            actor=self.user,
        )
        return location

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Location:
        location = self.get(code=code)
        before = self._snapshot(location)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_city = kwargs.get("city", location.city)
        new_country = kwargs.get("country", location.country)
        if (
            new_city != location.city or new_country != location.country
        ) and selectors.location_exists(new_city, new_country, exclude_pk=location.pk):
            raise AlreadyExistsException(
                detail=f"A location for '{new_city}, {new_country}' already exists."
            )

        if "city" in kwargs:
            location.city = kwargs["city"]
            update_fields.append("city")

        if "country" in kwargs:
            location.country = kwargs["country"]
            update_fields.append("country")

        if "is_active" in kwargs:
            location.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        if "is_default" in kwargs:
            location.is_default = kwargs["is_default"]
            update_fields.append("is_default")

        location.updated_by = self.user
        location.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=location.code,
            before=before,
            after=self._snapshot(location),
            actor=self.user,
        )
        return location

    @transaction.atomic
    def activate(self, code: str) -> Location:
        location = self.get(code=code)
        if not location.is_active:
            before = self._snapshot(location)
            location.is_active = True
            location.updated_by = self.user
            location.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=location.code,
                before=before,
                after=self._snapshot(location),
                actor=self.user,
            )
        return location

    @transaction.atomic
    def deactivate(self, code: str) -> Location:
        location = self.get(code=code)
        if location.is_active:
            before = self._snapshot(location)
            location.is_active = False
            location.updated_by = self.user
            location.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=location.code,
                before=before,
                after=self._snapshot(location),
                actor=self.user,
            )
        return location

    @transaction.atomic
    def set_default(self, code: str) -> Location:
        location = self.get(code=code)
        if not location.is_default:
            before = self._snapshot(location)
            Location.objects.exclude(pk=location.pk).filter(is_default=True).update(
                is_default=False
            )
            location.is_default = True
            location.updated_by = self.user
            location.save(update_fields=["is_default", "updated_by", "updated_at"])
            AuditService.log_set_default(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=location.code,
                before=before,
                after=self._snapshot(location),
                actor=self.user,
            )
        return location

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        location = self.get(code=code)
        location_code = location.code
        before = self._snapshot(location)
        location.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=location_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {
                "code": loc.code,
                "city": loc.city,
                "country": loc.country,
                "is_default": loc.is_default,
            }
            for loc in selectors.get_location_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_location_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class LocationImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 1_000
    MAX_IMPORT_FILE_SIZE_MB = 5

    def validate_file(self, file) -> None:
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
        city = (row.get("city") or "").strip()
        country = (row.get("country") or "").strip()
        if not city:
            errors.append(
                {"row": row_num, "field": "city", "message": "City is required."}
            )
        elif len(city) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "city",
                    "message": "City must be 100 characters or fewer.",
                }
            )
        if not country:
            errors.append(
                {"row": row_num, "field": "country", "message": "Country is required."}
            )
        elif len(country) > 100:
            errors.append(
                {
                    "row": row_num,
                    "field": "country",
                    "message": "Country must be 100 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"city", "country"}
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
        location_svc = LocationService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            city = row["city"].strip()
            country = row["country"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            is_default_raw = (row.get("is_default") or "false").strip().lower()
            is_default = is_default_raw in ("true", "1", "yes")

            if selectors.location_exists(city, country):
                errors.append(
                    {
                        "row": row_num,
                        "field": "city",
                        "message": (
                            f"A location for '{city}, {country}' already exists."
                        ),
                    }
                )
                continue

            if not dry_run:
                location_svc.create(
                    city=city,
                    country=country,
                    is_active=is_active,
                    is_default=is_default,
                )

            created_rows.append(
                {"row": row_num, "field": "city", "message": f"{city}, {country}"}
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class LocationExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "city": "City",
        "country": "Country",
        "is_active": "Active",
        "is_default": "Default",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "city",
        "country",
        "is_active",
        "is_default",
        "created_at",
    ]
    EXPORT_FILENAME = "locations_export"
    EXPORT_MODULE_NAME = "Locations"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        qs = selectors.get_all_locations()
        if filters:
            is_active_raw = filters.get("is_active")
            if is_active_raw in (None, ""):
                qs = qs.filter(is_active=True)
            elif str(is_active_raw).lower() != "all":
                qs = qs.filter(
                    is_active=str(is_active_raw).lower() not in ("false", "0")
                )
            search = (filters.get("search") or "").strip()
            if search:
                qs = qs.filter(city__icontains=search) | qs.filter(
                    country__icontains=search
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
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )
