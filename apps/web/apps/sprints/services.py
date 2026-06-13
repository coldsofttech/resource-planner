from __future__ import annotations

import csv
import io
import os
from datetime import date

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone as tz

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
from apps.financial_years.models import FinancialYear
from apps.sprints import selectors
from apps.sprints.constants import SprintStatus
from apps.sprints.engine import SprintGenerationEngine
from apps.sprints.models import Sprint


class SprintService(AuditableService, FilterableQueryService):
    _MODULE = "sprints"
    _RESOURCE_TYPE = "sprint"

    filterable_fields: dict[str, str] = {
        "status": "status",
        "financial_year": "financial_year__code",
        "is_closed": "is_closed",
        "is_overridden": "is_overridden",
        "month": "month",
    }
    search_fields: list[str] = ["name", "code", "sprint_number"]
    sortable_fields: list[str] = [
        "sprint_number",
        "name",
        "start_date",
        "end_date",
        "month",
        "status",
        "is_active",
        "is_closed",
        "created_at",
    ]
    default_ordering: list[str] = ["sprint_number"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_sprints()

    def _snapshot(self, obj: Sprint) -> dict:
        return {
            "code": obj.code,
            "sprint_number": obj.sprint_number,
            "name": obj.name,
            "financial_year": obj.financial_year_id,
            "start_date": str(obj.start_date),
            "end_date": str(obj.end_date),
            "month": obj.month,
            "status": obj.status,
            "is_active": obj.is_active,
            "is_overridden": obj.is_overridden,
            "is_closed": obj.is_closed,
            "note": obj.note,
        }

    def get(self, code: str, *args, **kwargs) -> Sprint:
        obj = selectors.get_sprint_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=code
            )
        return obj

    def get_active(self) -> Sprint:
        obj = selectors.get_in_progress_sprint()
        if obj is None:
            raise NotFoundException(
                resource="Sprint",
                lookup_field="status",
                lookup_value=SprintStatus.IN_PROGRESS,
            )
        return obj

    def _retire_current_in_progress(self, exclude_pk: int | None = None) -> None:
        qs = Sprint.objects.filter(status=SprintStatus.IN_PROGRESS)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        for retiring in qs:
            before = self._snapshot(retiring)
            retiring.status = SprintStatus.COMPLETED
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
        fy_code: str,
        sprint_number: int,
        name: str = "",
        start_date: date,
        end_date: date,
        status: str = SprintStatus.FUTURE,
        note: str = "",
        is_active: bool = True,
    ) -> Sprint:
        try:
            financial_year = FinancialYear.objects.get(code=fy_code)
        except FinancialYear.DoesNotExist as exc:
            raise NotFoundException(
                resource="Financial Year", lookup_field="code", lookup_value=fy_code
            ) from exc

        if not name:
            try:
                from apps.configurations.selectors import Sprint as SprintConfig

                prefix = SprintConfig.get_sprint_name_prefix()
            except Exception:
                prefix = "Sprint"
            name = f"{prefix} {sprint_number}"

        self._validate_dates(start_date, end_date)
        self._validate_dates_within_fy(start_date, end_date, financial_year)
        if selectors.has_overlapping_sprint(
            start_date, end_date, fy_pk=financial_year.pk
        ):
            raise ValidationException(
                "The date range overlaps with an existing sprint "
                "in this financial year."
            )
        if status == SprintStatus.IN_PROGRESS:
            self._retire_current_in_progress()

        obj = Sprint.objects.create(
            financial_year=financial_year,
            sprint_number=sprint_number,
            name=name,
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
    def update(self, code: str, **kwargs) -> Sprint:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at", "is_overridden"]

        new_start = kwargs.get("start_date", obj.start_date)
        new_end = kwargs.get("end_date", obj.end_date)
        dates_changed = new_start != obj.start_date or new_end != obj.end_date

        if dates_changed:
            self._validate_dates(new_start, new_end)
            self._validate_dates_within_fy(new_start, new_end, obj.financial_year)
            if selectors.has_overlapping_sprint(
                new_start, new_end, fy_pk=obj.financial_year_id, exclude_pk=obj.pk
            ):
                raise ValidationException(
                    "The date range overlaps with an existing sprint in this "
                    "financial year."
                )

        if "start_date" in kwargs:
            obj.start_date = kwargs["start_date"]
            update_fields.append("start_date")
        if "end_date" in kwargs:
            obj.end_date = kwargs["end_date"]
            update_fields.append("end_date")
        if dates_changed:
            update_fields += ["month"]
        if "name" in kwargs:
            obj.name = kwargs["name"]
            update_fields.append("name")
        if "status" in kwargs:
            new_status = kwargs["status"]
            if new_status == SprintStatus.IN_PROGRESS:
                self._retire_current_in_progress(exclude_pk=obj.pk)
            obj.status = new_status
            update_fields.append("status")
        if "note" in kwargs:
            obj.note = kwargs["note"]
            update_fields.append("note")
        if "is_active" in kwargs:
            obj.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        obj.is_overridden = True
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
    def activate(self, code: str) -> Sprint:
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
    def deactivate(self, code: str) -> Sprint:
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
    def set_active(self, code: str) -> Sprint:
        """Transition the sprint's status to In Progress.

        Retires any currently IN_PROGRESS sprint to COMPLETED first,
        ensuring only one sprint is IN_PROGRESS at any time.
        """
        obj = self.get(code=code)
        self._retire_current_in_progress(exclude_pk=obj.pk)
        if obj.status != SprintStatus.IN_PROGRESS:
            before = self._snapshot(obj)
            obj.status = SprintStatus.IN_PROGRESS
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
    def close(self, code: str, *, lock: bool = True) -> Sprint:
        """Lock or unlock a sprint.

        lock=True  → sets is_closed=True, records closed_on and closed_by.
        lock=False → clears is_closed, closed_on, and closed_by.
        """
        obj = self.get(code=code)
        before = self._snapshot(obj)
        obj.is_closed = lock
        obj.closed_on = tz.now() if lock else None
        obj.closed_by = self.user if lock else None
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "is_closed",
                "closed_on",
                "closed_by",
                "updated_by",
                "updated_at",
            ]
        )
        action = "locked" if lock else "unlocked"
        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after={**self._snapshot(obj), "action": action},
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        sprint_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=sprint_code,
            before=before,
            actor=self.user,
        )

    def options(self, fy_code: str | None = None) -> list[dict]:
        return [
            {
                "code": s.code,
                "sprint_number": s.sprint_number,
                "name": s.name,
                "start_date": str(s.start_date),
                "end_date": str(s.end_date),
                "month": s.month,
                "status": s.status,
            }
            for s in selectors.get_sprint_options(fy_code=fy_code)
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_sprint_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    @transaction.atomic
    def generate(self, fy_code: str) -> list[Sprint]:
        """Generate all sprints for a given financial year.

        Uses SprintGenerationEngine to compute the sprint windows and bulk-creates
        all sprints. Raises ValidationException if any sprints already exist
        for the financial year.
        """
        try:
            financial_year = FinancialYear.objects.get(code=fy_code)
        except FinancialYear.DoesNotExist as exc:
            raise NotFoundException(
                resource="Financial Year", lookup_field="code", lookup_value=fy_code
            ) from exc

        existing_count = Sprint.objects.filter(financial_year=financial_year).count()
        if existing_count > 0:
            raise ValidationException(
                f"Sprints already exist for financial year '{fy_code}'. "
                "Delete existing sprints before generating new ones."
            )

        next_number = selectors.get_max_sprint_number() + 1
        planned = SprintGenerationEngine.plan(
            fy_start=financial_year.start_date,
            fy_end=financial_year.end_date,
            next_sprint_number=next_number,
        )

        created: list[Sprint] = []
        for item in planned:
            obj = Sprint.objects.create(
                financial_year=financial_year,
                sprint_number=item["sprint_number"],
                name=item["name"],
                start_date=item["start_date"],
                end_date=item["end_date"],
                status=item["status"],
                is_active=True,
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
            created.append(obj)

        return created

    @staticmethod
    def _validate_dates(start_date: date, end_date: date) -> None:
        if end_date <= start_date:
            raise ValidationException("End date must be after start date.")

    @staticmethod
    def _validate_dates_within_fy(
        start_date: date, end_date: date, financial_year
    ) -> None:
        if start_date < financial_year.start_date or end_date > financial_year.end_date:
            raise ValidationException(
                f"Sprint dates must fall within the financial year "
                f"{financial_year.code} "
                f"({financial_year.start_date} – {financial_year.end_date})."
            )


class CapacityService(AuditableService):
    _MODULE = "sprints"
    _RESOURCE_TYPE = "capacity"

    def get_for_sprint(self, sprint_code: str):

        sprint = SprintService(user=self.user).get(code=sprint_code)
        return selectors.get_capacity_for_sprint(sprint)

    @transaction.atomic
    def rebuild(self, sprint_code: str) -> int:
        from apps.sprints.engine import SprintCapacityEngine

        sprint = SprintService(user=self.user).get(code=sprint_code)
        return SprintCapacityEngine.rebuild_for_sprint(sprint, actor=self.user)


class SprintImportService(ImportService):
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
        for field in ("fy_code", "sprint_number", "start_date", "end_date"):
            if not (row.get(field) or "").strip():
                errors.append(
                    {"row": row_num, "field": field, "message": f"{field} is required."}
                )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"fy_code", "sprint_number", "start_date", "end_date"}
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
        svc = SprintService(user=self.user)
        valid_statuses = {s[0] for s in SprintStatus.CHOICES}

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            fy_code = row["fy_code"].strip()
            try:
                financial_year = FinancialYear.objects.get(code=fy_code)
            except FinancialYear.DoesNotExist:
                errors.append(
                    {
                        "row": row_num,
                        "field": "fy_code",
                        "message": f"Financial year '{fy_code}' not found.",
                    }
                )
                continue

            try:
                sprint_number = int(row["sprint_number"].strip())
                start_date = date.fromisoformat(row["start_date"].strip())
                end_date = date.fromisoformat(row["end_date"].strip())
            except (ValueError, KeyError):
                errors.append(
                    {
                        "row": row_num,
                        "field": "sprint_number",
                        "message": (
                            "Invalid value. Check sprint_number and "
                            "date formats (YYYY-MM-DD)."
                        ),
                    }
                )
                continue

            name_raw = (row.get("name") or "").strip()
            status_raw = (row.get("status") or SprintStatus.FUTURE).strip().lower()
            status = status_raw if status_raw in valid_statuses else SprintStatus.FUTURE
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            note = (row.get("note") or "").strip()

            if selectors.has_overlapping_sprint(
                start_date, end_date, fy_pk=financial_year.pk
            ):
                errors.append(
                    {
                        "row": row_num,
                        "field": "start_date",
                        "message": (
                            "Date range overlaps with an existing sprint "
                            "in this financial year."
                        ),
                    }
                )
                continue

            if not dry_run:
                svc.create(
                    fy_code=fy_code,
                    sprint_number=sprint_number,
                    name=name_raw,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    note=note,
                    is_active=is_active,
                )

            created_rows.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": f"{name_raw}: {start_date} → {end_date}",
                }
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class SprintExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "sprint_number": "Sprint Number",
        "name": "Name",
        "financial_year": "Financial Year",
        "start_date": "Start Date",
        "end_date": "End Date",
        "month": "Month",
        "status": "Status",
        "is_active": "Active",
        "is_overridden": "Overridden",
        "is_closed": "Closed",
        "closed_on": "Closed On",
        "closed_by": "Closed By",
        "note": "Note",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "sprint_number",
        "name",
        "financial_year",
        "start_date",
        "end_date",
        "month",
        "status",
        "is_active",
        "is_closed",
    ]
    EXPORT_FILENAME = "sprints_export"
    EXPORT_MODULE_NAME = "Sprints"

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

        qs = selectors.get_all_sprints()
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
            fy_code = (filters.get("financial_year") or "").strip()
            if fy_code:
                qs = qs.filter(financial_year__code=fy_code)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

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
