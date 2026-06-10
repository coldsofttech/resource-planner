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
from apps.leaves import selectors
from apps.leaves.constants import HalfDayPeriod
from apps.leaves.engine import LeaveEngine
from apps.leaves.models import Leave
from apps.users.models import User


class LeaveService(AuditableService, FilterableQueryService):
    _MODULE = "leaves"
    _RESOURCE_TYPE = "leave"

    filterable_fields: dict[str, str] = {
        "member": "member__profile__code",
        "is_half_day": "is_half_day",
    }
    search_fields: list[str] = [
        "member__email",
        "member__first_name",
        "member__last_name",
    ]
    sortable_fields: list[str] = ["start_date", "end_date", "days", "created_at"]
    default_ordering: list[str] = ["-start_date"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_all_leaves()

    def _snapshot(self, leave: Leave) -> dict:
        return {
            "code": leave.code,
            "member": leave.member_id,
            "start_date": str(leave.start_date),
            "end_date": str(leave.end_date),
            "is_half_day": leave.is_half_day,
            "half_day_period": leave.half_day_period,
            "days": str(leave.days),
        }

    def get(self, code: str, *args, **kwargs) -> Leave:
        obj = selectors.get_leave_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Leave", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        member_code: str,
        start_date: datetime.date,
        end_date: datetime.date,
        is_half_day: bool = False,
        half_day_period: str | None = None,
        note: str = "",
    ) -> Leave:
        member = self._resolve_member(member_code)
        self._validate_dates(start_date, end_date, is_half_day, half_day_period)
        if selectors.leave_overlaps(member.pk, start_date, end_date):
            raise AlreadyExistsException(
                detail="An overlapping leave already exists for this member."
            )
        days = LeaveEngine.calculate_days(
            member_id=member.pk,
            start_date=start_date,
            end_date=end_date,
            is_half_day=is_half_day,
        )
        leave = Leave.objects.create(
            member=member,
            start_date=start_date,
            end_date=end_date,
            is_half_day=is_half_day,
            half_day_period=half_day_period if is_half_day else None,
            days=days,
            note=note,
            created_by=self.user,
            updated_by=self.user,
        )
        LeaveEngine.sync_day_entries(leave)
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=leave.code,
            after=self._snapshot(leave),
            actor=self.user,
        )
        return leave

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Leave:
        leave = self.get(code=code)
        before = self._snapshot(leave)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_start = kwargs.get("start_date", leave.start_date)
        new_end = kwargs.get("end_date", leave.end_date)
        new_is_half_day = kwargs.get("is_half_day", leave.is_half_day)
        new_half_day_period = kwargs.get("half_day_period", leave.half_day_period)

        self._validate_dates(new_start, new_end, new_is_half_day, new_half_day_period)

        if selectors.leave_overlaps(
            leave.member_id, new_start, new_end, exclude_pk=leave.pk
        ):
            raise AlreadyExistsException(
                detail="An overlapping leave already exists for this member."
            )

        if "start_date" in kwargs:
            leave.start_date = new_start
            update_fields.append("start_date")
        if "end_date" in kwargs:
            leave.end_date = new_end
            update_fields.append("end_date")
        if "is_half_day" in kwargs:
            leave.is_half_day = new_is_half_day
            update_fields.append("is_half_day")
        if "half_day_period" in kwargs or "is_half_day" in kwargs:
            leave.half_day_period = new_half_day_period if new_is_half_day else None
            update_fields.append("half_day_period")
        if "note" in kwargs:
            leave.note = kwargs["note"]
            update_fields.append("note")

        if any(k in kwargs for k in ("start_date", "end_date", "is_half_day")):
            leave.days = LeaveEngine.calculate_days(
                member_id=leave.member_id,
                start_date=leave.start_date,
                end_date=leave.end_date,
                is_half_day=leave.is_half_day,
            )
            update_fields.append("days")

        leave.updated_by = self.user
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for f in update_fields:
            if f not in seen:
                seen.add(f)
                deduped.append(f)
        leave.save(update_fields=deduped)
        LeaveEngine.sync_day_entries(leave)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=leave.code,
            before=before,
            after=self._snapshot(leave),
            actor=self.user,
        )
        return leave

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        leave = self.get(code=code)
        leave_code = leave.code
        before = self._snapshot(leave)
        leave.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=leave_code,
            before=before,
            actor=self.user,
        )

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_leave_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    @staticmethod
    def _resolve_member(member_code: str) -> User:
        from apps.users.models import UserProfile

        try:
            profile = UserProfile.objects.select_related("user").get(code=member_code)
            return profile.user
        except UserProfile.DoesNotExist as exc:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            ) from exc

    @staticmethod
    def _validate_dates(
        start_date: datetime.date,
        end_date: datetime.date,
        is_half_day: bool,
        half_day_period: str | None,
    ) -> None:
        if is_half_day:
            if start_date != end_date:
                raise ValidationException(
                    "Half-day leave must have the same start and end date."
                )
            if half_day_period and half_day_period not in HalfDayPeriod.values:
                raise ValidationException(
                    f"Invalid half_day_period. Choices: "
                    f"{', '.join(HalfDayPeriod.values)}."
                )
        else:
            if end_date < start_date:
                raise ValidationException("End date must be on or after start date.")


class LeaveImportService(ImportService):
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
                f"File too large. Maximum allowed size: "
                f"{self.MAX_IMPORT_FILE_SIZE_MB} MB."
            )

    def validate_row(self, row: dict, row_num: int) -> list[dict]:
        errors: list[dict] = []
        member_code = (row.get("member_code") or "").strip()
        start_str = (row.get("start_date") or "").strip()
        end_str = (row.get("end_date") or "").strip()
        is_half_str = (row.get("is_half_day") or "false").strip().lower()

        if not member_code:
            errors.append(
                {
                    "row": row_num,
                    "field": "member_code",
                    "message": "Member code is required.",
                }
            )
        if not start_str:
            errors.append(
                {
                    "row": row_num,
                    "field": "start_date",
                    "message": "Start date is required.",
                }
            )
        else:
            try:
                datetime.date.fromisoformat(start_str)
            except ValueError:
                errors.append(
                    {
                        "row": row_num,
                        "field": "start_date",
                        "message": "Start date must be YYYY-MM-DD.",
                    }
                )
        if not end_str:
            errors.append(
                {
                    "row": row_num,
                    "field": "end_date",
                    "message": "End date is required.",
                }
            )
        else:
            try:
                datetime.date.fromisoformat(end_str)
            except ValueError:
                errors.append(
                    {
                        "row": row_num,
                        "field": "end_date",
                        "message": "End date must be YYYY-MM-DD.",
                    }
                )
        if is_half_str not in ("true", "false", "yes", "no", "1", "0"):
            errors.append(
                {
                    "row": row_num,
                    "field": "is_half_day",
                    "message": "is_half_day must be true or false.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"member_code", "start_date", "end_date"}
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

        from apps.users.models import UserProfile

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        leave_svc = LeaveService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            member_code = row["member_code"].strip()
            start_date = datetime.date.fromisoformat(row["start_date"].strip())
            end_date = datetime.date.fromisoformat(row["end_date"].strip())
            is_half_str = (row.get("is_half_day") or "false").strip().lower()
            is_half_day = is_half_str in ("true", "yes", "1")
            half_day_period = (row.get("half_day_period") or "").strip() or None
            note = (row.get("note") or "").strip()

            try:
                profile = UserProfile.objects.select_related("user").get(
                    code=member_code
                )
            except UserProfile.DoesNotExist:
                errors.append(
                    {
                        "row": row_num,
                        "field": "member_code",
                        "message": f"Member '{member_code}' not found.",
                    }
                )
                continue

            try:
                LeaveService._validate_dates(
                    start_date, end_date, is_half_day, half_day_period
                )
            except ValidationException as exc:
                errors.append(
                    {"row": row_num, "field": "dates", "message": str(exc.detail)}
                )
                continue

            if selectors.leave_overlaps(profile.user_id, start_date, end_date):
                errors.append(
                    {
                        "row": row_num,
                        "field": "dates",
                        "message": "Overlapping leave exists for this member.",
                    }
                )
                continue

            if not dry_run:
                leave_svc.create(
                    member_code=member_code,
                    start_date=start_date,
                    end_date=end_date,
                    is_half_day=is_half_day,
                    half_day_period=half_day_period,
                    note=note,
                )

            created_rows.append(
                {
                    "row": row_num,
                    "field": "member_code",
                    "message": f"{member_code}: {start_date} – {end_date}",
                }
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class LeaveExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "member": "Member",
        "start_date": "Start Date",
        "end_date": "End Date",
        "is_half_day": "Half Day",
        "half_day_period": "Period",
        "days": "Days",
        "note": "Note",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "member",
        "start_date",
        "end_date",
        "is_half_day",
        "half_day_period",
        "days",
        "note",
        "created_at",
    ]
    EXPORT_FILENAME = "leaves_export"
    EXPORT_MODULE_NAME = "Leaves"

    def _get_field_value(self, obj: Leave, field: str) -> str:
        if field == "member":
            try:
                profile = obj.member.profile
                return (
                    profile.display_name
                    or obj.member.get_full_name()
                    or obj.member.email
                )
            except Exception:
                return obj.member.email
        if field == "half_day_period":
            val = obj.half_day_period
            if not val:
                return ""
            try:
                return HalfDayPeriod(val).label
            except ValueError:
                return val
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

        qs = selectors.get_all_leaves()
        if filters:
            member = (filters.get("member") or "").strip()
            if member:
                qs = qs.filter(member__profile__code=member)
            search = (filters.get("search") or "").strip()
            if search:
                from django.db.models import Q

                qs = qs.filter(
                    Q(member__email__icontains=search)
                    | Q(member__first_name__icontains=search)
                    | Q(member__last_name__icontains=search)
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
