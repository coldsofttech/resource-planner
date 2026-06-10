from __future__ import annotations

import csv
import io
import os
from datetime import date

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from apps.core.services import (
    AuditableService,
    ExportService,
    FilterableQueryService,
    ImportService,
)
from apps.financial_years import selectors
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear


class FinancialYearService(AuditableService, FilterableQueryService):
    _MODULE = "financial_years"
    _RESOURCE_TYPE = "financial_year"

    filterable_fields: dict[str, str] = {
        "status": "status",
    }
    search_fields: list[str] = ["long_fy", "short_fy"]
    sortable_fields: list[str] = [
        "long_fy",
        "short_fy",
        "start_date",
        "end_date",
        "span_days",
        "status",
        "is_active",
        "created_at",
    ]
    default_ordering: list[str] = ["-start_date"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_financial_years()

    def _snapshot(self, obj: FinancialYear) -> dict:
        return {
            "code": obj.code,
            "long_fy": obj.long_fy,
            "short_fy": obj.short_fy,
            "start_date": str(obj.start_date),
            "end_date": str(obj.end_date),
            "span_days": obj.span_days,
            "status": obj.status,
            "is_active": obj.is_active,
            "note": obj.note,
        }

    def get(self, code: str, *args, **kwargs) -> FinancialYear:
        obj = selectors.get_financial_year_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Financial Year", lookup_field="code", lookup_value=code
            )
        return obj

    def get_active(self) -> FinancialYear:
        obj = selectors.get_in_progress_financial_year()
        if obj is None:
            raise NotFoundException(
                resource="Financial Year",
                lookup_field="status",
                lookup_value=FinancialYearStatus.IN_PROGRESS,
            )
        return obj

    def _retire_current_in_progress(self, exclude_pk: int | None = None) -> None:
        """Transition any IN_PROGRESS financial year to COMPLETED.

        Called before promoting a new FY to IN_PROGRESS to enforce the
        single-active-year invariant.
        """
        qs = FinancialYear.objects.filter(status=FinancialYearStatus.IN_PROGRESS)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        for retiring in qs:
            before = self._snapshot(retiring)
            retiring.status = FinancialYearStatus.COMPLETED
            retiring.updated_by = self.user
            retiring.save(update_fields=["status", "updated_by", "updated_at"])
            AuditService.log_update(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=retiring.code,
                before=before,
                after=self._snapshot(retiring),
                actor=self.user,
            )

    @transaction.atomic
    def create(
        self,
        *,
        start_date: date,
        end_date: date,
        status: str = FinancialYearStatus.FUTURE,
        note: str = "",
        is_active: bool = True,
    ) -> FinancialYear:
        self._validate_dates(start_date, end_date)
        if selectors.has_overlapping_financial_year(start_date, end_date):
            raise ValidationException(
                "The date range overlaps with an existing financial year."
            )
        if status == FinancialYearStatus.IN_PROGRESS:
            self._retire_current_in_progress()

        obj = FinancialYear.objects.create(
            start_date=start_date,
            end_date=end_date,
            status=status,
            note=note,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> FinancialYear:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_start = kwargs.get("start_date", obj.start_date)
        new_end = kwargs.get("end_date", obj.end_date)
        dates_changed = new_start != obj.start_date or new_end != obj.end_date

        if dates_changed:
            self._validate_dates(new_start, new_end)
            if selectors.has_overlapping_financial_year(
                new_start, new_end, exclude_pk=obj.pk
            ):
                raise ValidationException(
                    "The date range overlaps with an existing financial year."
                )

        if "start_date" in kwargs:
            obj.start_date = kwargs["start_date"]
            update_fields.append("start_date")
        if "end_date" in kwargs:
            obj.end_date = kwargs["end_date"]
            update_fields.append("end_date")

        if dates_changed:
            # Trigger recalculation of derived fields via model.save() override
            update_fields += ["long_fy", "short_fy", "span_days"]

        if "status" in kwargs:
            new_status = kwargs["status"]
            if new_status == FinancialYearStatus.IN_PROGRESS:
                self._retire_current_in_progress(exclude_pk=obj.pk)
            obj.status = new_status
            update_fields.append("status")
        if "note" in kwargs:
            obj.note = kwargs["note"]
            update_fields.append("note")
        if "is_active" in kwargs:
            obj.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def activate(self, code: str) -> FinancialYear:
        obj = self.get(code=code)
        if not obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def deactivate(self, code: str) -> FinancialYear:
        obj = self.get(code=code)
        if obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = False
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def set_active(self, code: str) -> FinancialYear:
        """Set the financial year's status to In Progress.

        Retires any currently IN_PROGRESS financial year to COMPLETED first,
        ensuring only one financial year is IN_PROGRESS at any time.
        """
        obj = self.get(code=code)
        self._retire_current_in_progress(exclude_pk=obj.pk)
        if obj.status != FinancialYearStatus.IN_PROGRESS:
            before = self._snapshot(obj)
            obj.status = FinancialYearStatus.IN_PROGRESS
            obj.updated_by = self.user
            obj.save(update_fields=["status", "updated_by", "updated_at"])
            AuditService.log_update(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        fy_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=fy_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {
                "code": fy.code,
                "long_fy": fy.long_fy,
                "short_fy": fy.short_fy,
                "start_date": str(fy.start_date),
                "end_date": str(fy.end_date),
                "status": fy.status,
            }
            for fy in selectors.get_financial_year_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_financial_year_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        if end_date <= start_date:
            raise ValidationException("End date must be after start date.")


class FinancialYearImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 500
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
        start_raw = (row.get("start_date") or "").strip()
        end_raw = (row.get("end_date") or "").strip()

        if not start_raw:
            errors.append(
                {
                    "row": row_num,
                    "field": "start_date",
                    "message": "start_date is required.",
                }
            )
        if not end_raw:
            errors.append(
                {
                    "row": row_num,
                    "field": "end_date",
                    "message": "end_date is required.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"start_date", "end_date"}
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
        fy_svc = FinancialYearService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            try:
                from datetime import date as date_type

                start_date = date_type.fromisoformat(row["start_date"].strip())
                end_date = date_type.fromisoformat(row["end_date"].strip())
            except (ValueError, KeyError):
                errors.append(
                    {
                        "row": row_num,
                        "field": "start_date",
                        "message": "Invalid date format. Use YYYY-MM-DD.",
                    }
                )
                continue

            status_raw = (
                (row.get("status") or FinancialYearStatus.FUTURE).strip().lower()
            )
            valid_statuses = {s[0] for s in FinancialYearStatus.CHOICES}
            status = (
                status_raw
                if status_raw in valid_statuses
                else FinancialYearStatus.FUTURE
            )

            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            note = (row.get("note") or "").strip()

            if selectors.has_overlapping_financial_year(start_date, end_date):
                errors.append(
                    {
                        "row": row_num,
                        "field": "start_date",
                        "message": (
                            "Date range overlaps with an existing financial year."
                        ),
                    }
                )
                continue

            if not dry_run:
                fy_svc.create(
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    note=note,
                    is_active=is_active,
                )

            created_rows.append(
                {
                    "row": row_num,
                    "field": "long_fy",
                    "message": f"{start_date} → {end_date}",
                }
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class FinancialYearExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "long_fy": "Financial Year (Long)",
        "short_fy": "Financial Year (Short)",
        "start_date": "Start Date",
        "end_date": "End Date",
        "span_days": "Span (Days)",
        "status": "Status",
        "is_active": "Active",
        "note": "Note",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "long_fy",
        "short_fy",
        "start_date",
        "end_date",
        "span_days",
        "status",
        "is_active",
    ]
    EXPORT_FILENAME = "financial_years_export"
    EXPORT_MODULE_NAME = "Financial Years"

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

        qs = selectors.get_all_financial_years()
        if filters:
            is_active_raw = filters.get("is_active")
            if is_active_raw in (None, ""):
                qs = qs.filter(is_active=True)
            elif str(is_active_raw).lower() != "all":
                qs = qs.filter(
                    is_active=str(is_active_raw).lower() not in ("false", "0")
                )
            status_filter = filters.get("status", "").strip()
            if status_filter:
                qs = qs.filter(status=status_filter)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(long_fy__icontains=search) | Q(short_fy__icontains=search)
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
            "Allowed: csv, xlsx, pdf, json."
        )
