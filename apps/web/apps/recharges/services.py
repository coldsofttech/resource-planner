from __future__ import annotations

import csv
import io
import os
import re

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
from apps.recharges import selectors
from apps.recharges.models import ProjectTypeMapping, RechargeType

_UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class RechargeTypeService(AuditableService, FilterableQueryService):
    _MODULE = "recharges"
    _RESOURCE_TYPE = "recharge_type"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "is_active", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_recharge_types()

    def _snapshot(self, recharge_type: RechargeType) -> dict:
        return {
            "code": recharge_type.code,
            "name": recharge_type.name,
            "description": recharge_type.description,
            "is_active": recharge_type.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> RechargeType:
        obj = selectors.get_recharge_type_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="RechargeType", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        description: str = "",
        is_active: bool = True,
    ) -> RechargeType:
        if selectors.recharge_type_exists(name):
            raise AlreadyExistsException(
                detail=f"A recharge type named '{name}' already exists."
            )
        obj = RechargeType.objects.create(
            name=name,
            description=description,
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
    def update(self, code: str, **kwargs) -> RechargeType:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_name = kwargs.get("name", obj.name)
        if new_name != obj.name and selectors.recharge_type_exists(
            new_name, exclude_pk=obj.pk
        ):
            raise AlreadyExistsException(
                detail=f"A recharge type named '{new_name}' already exists."
            )

        if "name" in kwargs:
            obj.name = kwargs["name"]
            update_fields.append("name")

        if "description" in kwargs:
            obj.description = kwargs["description"]
            update_fields.append("description")

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
    def activate(self, code: str) -> RechargeType:
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
    def deactivate(self, code: str) -> RechargeType:
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
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        recharge_type_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=recharge_type_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {"code": rt.code, "name": rt.name}
            for rt in selectors.get_recharge_type_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_recharge_type_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class RechargeTypeImportService(ImportService):
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
        if not name:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Recharge type name is required.",
                }
            )
        elif len(name) > 50:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Recharge type name must be 50 characters or fewer.",
                }
            )
        elif not _UPPER_SNAKE_RE.match(name):
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": (
                        "Name must be UPPER_SNAKE_CASE (e.g. PROJECT, BAU, HOLIDAY)."
                    ),
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
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
        svc = RechargeTypeService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")
            description = (row.get("description") or "").strip()

            if selectors.recharge_type_exists(name):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A recharge type named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                svc.create(
                    name=name,
                    description=description,
                    is_active=is_active,
                )

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class RechargeTypeExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Recharge Type Name",
        "description": "Description",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "description",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "recharge_types_export"
    EXPORT_MODULE_NAME = "Recharge Types"

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

        qs = selectors.get_all_recharge_types()
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
            "Allowed: csv, xlsx, pdf, json."
        )


class ProjectTypeMappingService(AuditableService, FilterableQueryService):
    _MODULE = "recharges"
    _RESOURCE_TYPE = "project_type_mapping"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["project_type__name"]
    sortable_fields: list[str] = ["project_type__name", "created_at"]
    default_ordering: list[str] = ["project_type__name"]
    filter_active_by_default: bool = False

    def __init__(self, user=None, request=None, recharge_type_code: str = ""):
        super().__init__(user=user, request=request)
        self._recharge_type_code = recharge_type_code

    def get_queryset(self):
        return selectors.get_all_project_type_mappings(self._recharge_type_code)

    def _get_recharge_type(self) -> RechargeType:
        obj = selectors.get_recharge_type_by_code(self._recharge_type_code)
        if obj is None:
            raise NotFoundException(
                resource="RechargeType",
                lookup_field="code",
                lookup_value=self._recharge_type_code,
            )
        return obj

    def _snapshot(self, mapping: ProjectTypeMapping) -> dict:
        return {
            "recharge_type_code": mapping.recharge_type.code,
            "project_type_code": mapping.project_type.code,
        }

    def get(self, pk: int, **kwargs) -> ProjectTypeMapping:
        obj = selectors.get_project_type_mapping_by_id(self._recharge_type_code, pk)
        if obj is None:
            raise NotFoundException(
                resource="ProjectTypeMapping",
                lookup_field="pk",
                lookup_value=str(pk),
            )
        return obj

    @transaction.atomic
    def create(self, *, project_type_code: str) -> ProjectTypeMapping:
        from apps.projects.selectors.project_type import get_project_type_by_code

        recharge_type = self._get_recharge_type()
        project_type = get_project_type_by_code(project_type_code)
        if project_type is None:
            raise ValidationException(f"Project type '{project_type_code}' not found.")
        if selectors.project_type_mapping_exists(recharge_type.pk, project_type.pk):
            raise AlreadyExistsException(
                detail=(
                    f"A mapping for project type '{project_type.name}' already exists "
                    "on this recharge type."
                )
            )
        obj = ProjectTypeMapping.objects.create(
            recharge_type=recharge_type,
            project_type=project_type,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=str(obj.pk),
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(
        self, pk: int, *, project_type_code: str, **kwargs
    ) -> ProjectTypeMapping:
        from apps.projects.selectors.project_type import get_project_type_by_code

        obj = self.get(pk=pk)
        before = self._snapshot(obj)

        new_project_type = get_project_type_by_code(project_type_code)
        if new_project_type is None:
            raise ValidationException(f"Project type '{project_type_code}' not found.")
        if selectors.project_type_mapping_exists(
            obj.recharge_type_id, new_project_type.pk, exclude_pk=obj.pk
        ):
            raise AlreadyExistsException(
                detail=(
                    f"A mapping for project type '{new_project_type.name}' already "
                    "exists on this recharge type."
                )
            )

        obj.project_type = new_project_type
        obj.updated_by = self.user
        obj.save(update_fields=["project_type", "updated_by", "updated_at"])

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=str(obj.pk),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, pk: int, **kwargs) -> None:
        obj = self.get(pk=pk)
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=str(pk),
            before=before,
            actor=self.user,
        )

    def stats(self, fields=None, **kwargs) -> dict:
        result = {"total": self.get_queryset().count()}
        if fields:
            return {k: v for k, v in result.items() if k in fields}
        return result


class ProjectTypeMappingImportService(ImportService):
    SUPPORTED_IMPORT_FORMATS = ["csv"]
    MAX_IMPORT_ROWS = 500
    MAX_IMPORT_FILE_SIZE_MB = 5

    def __init__(self, user=None, request=None, recharge_type_code: str = ""):
        super().__init__(user=user, request=request)
        self._recharge_type_code = recharge_type_code

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
        code = (row.get("project_type_code") or "").strip()
        if not code:
            errors.append(
                {
                    "row": row_num,
                    "field": "project_type_code",
                    "message": "Project type code is required.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        from apps.projects.selectors.project_type import get_project_type_by_code

        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"project_type_code"}
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

        recharge_type = selectors.get_recharge_type_by_code(self._recharge_type_code)
        if recharge_type is None:
            raise ValidationException(
                f"Recharge type '{self._recharge_type_code}' not found."
            )

        total = len(rows)
        created_rows: list[dict] = []
        errors: list[dict] = []
        svc = ProjectTypeMappingService(
            user=self.user, recharge_type_code=self._recharge_type_code
        )

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            project_type_code = row["project_type_code"].strip()
            project_type = get_project_type_by_code(project_type_code)
            if project_type is None:
                errors.append(
                    {
                        "row": row_num,
                        "field": "project_type_code",
                        "message": f"Project type '{project_type_code}' not found.",
                    }
                )
                continue

            if selectors.project_type_mapping_exists(recharge_type.pk, project_type.pk):
                errors.append(
                    {
                        "row": row_num,
                        "field": "project_type_code",
                        "message": (
                            f"Mapping for project type '{project_type.name}' already "
                            "exists."
                        ),
                    }
                )
                continue

            if not dry_run:
                svc.create(project_type_code=project_type_code)

            created_rows.append(
                {
                    "row": row_num,
                    "field": "project_type_code",
                    "message": project_type.name,
                }
            )

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class ProjectTypeMappingExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "project_type_code": "Project Type Code",
        "project_type_name": "Project Type Name",
        "recharge_type_code": "Recharge Type Code",
        "created_at": "Created On",
        "created_by": "Created By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "project_type_code",
        "project_type_name",
        "recharge_type_code",
        "created_at",
    ]
    EXPORT_FILENAME = "project_type_mappings_export"
    EXPORT_MODULE_NAME = "Project Type Mappings"

    def __init__(self, user=None, request=None, recharge_type_code: str = ""):
        super().__init__(user=user, request=request)
        self._recharge_type_code = recharge_type_code

    def _get_field_value(self, obj: ProjectTypeMapping, field: str) -> str:
        if field == "project_type_code":
            return obj.project_type.code
        if field == "project_type_name":
            return obj.project_type.name
        if field == "recharge_type_code":
            return obj.recharge_type.code
        if field == "created_by":
            u = obj.created_by
            if u is None:
                return ""
            return u.get_full_name() or u.email or str(u)
        if field == "created_at":
            val = obj.created_at
            return val.strftime("%Y-%m-%d %H:%M") if val else ""
        return ""

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

        qs = selectors.get_all_project_type_mappings(self._recharge_type_code)
        search = (filters or {}).get("search", "").strip()
        if search:
            qs = qs.filter(project_type__name__icontains=search)

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


class RechargeDetailService:
    """Populates RechargeDetail records from confirmed forecast import data."""

    def __init__(self, user: object) -> None:
        self.user = user

    def _sync_recharges(self, sprint_id: int, recharge_type: str) -> None:
        """Rebuild Recharge aggregate records for a sprint/type from RechargeDetail."""
        from decimal import Decimal

        from django.db.models import Sum

        from apps.projects.models.contact import ProjectContact
        from apps.recharges.models import Recharge, RechargeDetail

        Recharge.objects.filter(sprint_id=sprint_id, type=recharge_type).delete()

        groups = (
            RechargeDetail.objects.filter(sprint_id=sprint_id, type=recharge_type)
            .values("sprint_id", "type", "programme_id", "project_id")
            .annotate(agg_days=Sum("total_days"), agg_cost=Sum("total_cost"))
        )

        for g in groups:
            project_id = g["project_id"]

            recharge = Recharge(
                sprint_id=g["sprint_id"],
                type=g["type"],
                programme_id=g["programme_id"],
                project_id=project_id,
                total_days=g["agg_days"] or Decimal("0"),
                total_cost=g["agg_cost"] or Decimal("0"),
            )
            recharge.save()

            if project_id is not None:
                contacts = ProjectContact.objects.filter(project_id=project_id)
                recharge.finance_contacts.set(contacts.filter(role="finance"))
                recharge.project_contacts.set(contacts.filter(role="project"))

    def populate_from_sprint_forecast(self, sprint_id: int) -> int:
        """
        Delete existing forecast RechargeDetail entries for the sprint and
        recreate them from the latest confirmed SprintDataImport rows.
        Aggregated Recharge records are synced afterwards.

        Returns the number of RechargeDetail records created.
        """
        from decimal import ROUND_HALF_UP, Decimal

        from apps.configurations.selectors import Sprint as SprintConfig
        from apps.recharges.constants import RechargeType as RechargeTypeChoice
        from apps.recharges.models import RechargeDetail
        from apps.sprints.models import SprintDataImportConfirmed, SprintDataImportRow

        RechargeDetail.objects.filter(
            sprint_id=sprint_id, type=RechargeTypeChoice.FORECAST
        ).delete()

        # Identify the latest confirmed imports via SprintDataImportConfirmed
        latest_import_ids = list(
            SprintDataImportConfirmed.objects.filter(
                sprint_id=sprint_id, import_type="forecast"
            )
            .values_list("import_record_id", flat=True)
            .distinct()
        )
        if not latest_import_ids:
            self._sync_recharges(sprint_id, "forecast")
            return 0

        hours_per_day = SprintConfig.get_hours_per_day()
        per_day = (
            Decimal(str(hours_per_day * 3_600)) if hours_per_day > 0 else Decimal("0")
        )
        point_price = Decimal(str(SprintConfig.get_sprint_point_price()))

        def _days(efforts_str: str) -> Decimal:
            try:
                val = Decimal(str(efforts_str))
            except Exception:
                return Decimal("0")
            if val <= 0 or per_day <= 0:
                return Decimal("0")
            return (val / per_day).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rows = (
            SprintDataImportRow.objects.select_related(
                "import_record__team",
                "assignee_code",
                "assignee_code_override",
                "label_code__project__programme",
                "label_code_override__project__programme",
            )
            .filter(import_record_id__in=latest_import_ids, is_deleted=False)
            .order_by("import_record_id", "pk")
        )

        count = 0
        for row in rows:
            assignee = row.effective_assignee_code
            label = row.effective_label_code
            project = label.project if label is not None else None
            programme = project.programme if project is not None else None

            detail = RechargeDetail(
                sprint_id=sprint_id,
                team=row.import_record.team,
                assignee=assignee,
                programme=programme,
                project=project,
                label=label,
                type=RechargeTypeChoice.FORECAST,
                jira_id=row.effective_jira_id or "",
                title=row.effective_title or "",
                total_days=_days(row.effective_efforts),
                total_cost=_days(row.effective_efforts) * point_price,
                import_record=row.import_record,
                created_by=self.user,
                updated_by=self.user,
            )
            detail.save()
            count += 1

        self._sync_recharges(sprint_id, "forecast")
        return count
