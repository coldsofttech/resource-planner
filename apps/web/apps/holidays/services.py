from __future__ import annotations

import csv
import datetime
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
from apps.holidays import selectors
from apps.holidays.models import Holiday


class HolidayService(AuditableService, FilterableQueryService):
    _MODULE = "holidays"
    _RESOURCE_TYPE = "holiday"

    filterable_fields: dict[str, str] = {
        "location": "location__code",
        "year": "date__year",
    }
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "date", "created_at"]
    default_ordering: list[str] = ["location", "date"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_holidays()

    def _snapshot(self, holiday: Holiday) -> dict:
        return {
            "code": holiday.code,
            "name": holiday.name,
            "date": str(holiday.date),
            "location": holiday.location.code,
        }

    def get(self, code: str, *args, **kwargs) -> Holiday:
        obj = selectors.get_holiday_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Holiday", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        date: datetime.date,
        location_code: str,
    ) -> Holiday:
        from apps.locations.selectors import get_location_by_code

        location = get_location_by_code(location_code)
        if location is None:
            raise NotFoundException(
                resource="Location", lookup_field="code", lookup_value=location_code
            )
        if selectors.holiday_exists(location.pk, date):
            raise AlreadyExistsException(
                detail=f"A holiday for '{location}' on {date} already exists."
            )
        holiday = Holiday.objects.create(
            name=name,
            date=date,
            location=location,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=holiday.code,
            after=self._snapshot(holiday),
            actor=self.user,
        )
        return holiday

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Holiday:
        holiday = self.get(code=code)
        before = self._snapshot(holiday)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_location = holiday.location
        new_date = kwargs.get("date", holiday.date)

        if "location_code" in kwargs:
            from apps.locations.selectors import get_location_by_code

            new_location = get_location_by_code(kwargs["location_code"])
            if new_location is None:
                raise NotFoundException(
                    resource="Location",
                    lookup_field="code",
                    lookup_value=kwargs["location_code"],
                )

        if (
            new_location.pk != holiday.location.pk or new_date != holiday.date
        ) and selectors.holiday_exists(
            new_location.pk, new_date, exclude_pk=holiday.pk
        ):
            raise AlreadyExistsException(
                detail=f"A holiday for '{new_location}' on {new_date} already exists."
            )

        if "name" in kwargs:
            holiday.name = kwargs["name"]
            update_fields.append("name")

        if "date" in kwargs:
            holiday.date = kwargs["date"]
            update_fields.append("date")

        if "location_code" in kwargs:
            holiday.location = new_location
            update_fields.append("location")

        holiday.updated_by = self.user
        holiday.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=holiday.code,
            before=before,
            after=self._snapshot(holiday),
            actor=self.user,
        )
        return holiday

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        holiday = self.get(code=code)
        holiday_code = holiday.code
        before = self._snapshot(holiday)
        holiday.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=holiday_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> dict:
        year_range = selectors.get_holiday_year_range()
        return {
            "items": [
                {
                    "code": h.code,
                    "name": h.name,
                    "date": str(h.date),
                    "location": {
                        "code": h.location.code,
                        "city": h.location.city,
                        "country": h.location.country,
                    },
                }
                for h in selectors.get_holiday_options()
            ],
            "min_year": year_range[0] if year_range else None,
            "max_year": year_range[1] if year_range else None,
        }

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_holiday_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class HolidayImportService(ImportService):
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
        name = (row.get("name") or "").strip()
        date_str = (row.get("date") or "").strip()
        location_code = (row.get("location_code") or "").strip()

        if not name:
            errors.append(
                {"row": row_num, "field": "name", "message": "Name is required."}
            )
        elif len(name) > 120:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Name must be 120 characters or fewer.",
                }
            )

        if not date_str:
            errors.append(
                {"row": row_num, "field": "date", "message": "Date is required."}
            )
        else:
            try:
                datetime.date.fromisoformat(date_str)
            except ValueError:
                errors.append(
                    {
                        "row": row_num,
                        "field": "date",
                        "message": "Date must be in YYYY-MM-DD format.",
                    }
                )

        if not location_code:
            errors.append(
                {
                    "row": row_num,
                    "field": "location_code",
                    "message": "Location code is required.",
                }
            )

        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name", "date", "location_code"}
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

        from apps.locations.selectors import get_location_by_code

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        holiday_svc = HolidayService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            date = datetime.date.fromisoformat(row["date"].strip())
            location_code = row["location_code"].strip()

            location = get_location_by_code(location_code)
            if location is None:
                errors.append(
                    {
                        "row": row_num,
                        "field": "location_code",
                        "message": f"Location '{location_code}' not found.",
                    }
                )
                continue

            if selectors.holiday_exists(location.pk, date):
                errors.append(
                    {
                        "row": row_num,
                        "field": "date",
                        "message": (
                            f"A holiday for '{location}' on {date} already exists."
                        ),
                    }
                )
                continue

            if not dry_run:
                holiday_svc.create(
                    name=name,
                    date=date,
                    location_code=location_code,
                )

            created_rows.append(
                {"row": row_num, "field": "name", "message": f"{name} ({location})"}
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class HolidayExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Name",
        "date": "Date",
        "location": "Location",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "date",
        "location",
        "created_at",
    ]
    EXPORT_FILENAME = "holidays_export"
    EXPORT_MODULE_NAME = "Holidays"

    def _get_field_value(self, obj, field: str) -> str:
        if field == "location":
            loc = getattr(obj, "location", None)
            if loc:
                return f"{loc.city}, {loc.country}"
            return ""
        return super()._get_field_value(obj, field)

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

        qs = selectors.get_all_holidays()
        if filters:
            location = (filters.get("location") or "").strip()
            if location:
                qs = qs.filter(location__code=location)
            search = (filters.get("search") or "").strip()
            if search:
                qs = qs.filter(name__icontains=search)

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
