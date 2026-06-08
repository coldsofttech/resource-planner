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
from apps.teams import selectors
from apps.teams.models import Team


class TeamService(AuditableService, FilterableQueryService):
    _MODULE = "teams"
    _RESOURCE_TYPE = "team"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "is_active", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_teams()

    def _snapshot(self, team: Team) -> dict:
        return {
            "code": team.code,
            "name": team.name,
            "description": team.description,
            "is_active": team.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> Team:
        obj = selectors.get_team_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self, *, name: str, is_active: bool = True, description: str = ""
    ) -> Team:
        if selectors.team_name_exists(name):
            raise AlreadyExistsException(
                detail=f"A team named '{name}' already exists."
            )
        team = Team.objects.create(
            name=name,
            description=description,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=team.code,
            after=self._snapshot(team),
            actor=self.user,
        )
        return team

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Team:
        team = self.get(code=code)
        before = self._snapshot(team)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "name" in kwargs:
            new_name = kwargs["name"]
            if new_name != team.name and selectors.team_name_exists(
                new_name, exclude_pk=team.pk
            ):
                raise AlreadyExistsException(
                    detail=f"A team named '{new_name}' already exists."
                )
            team.name = new_name
            update_fields.append("name")

        if "description" in kwargs:
            team.description = kwargs["description"]
            update_fields.append("description")

        if "is_active" in kwargs:
            team.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        team.updated_by = self.user
        team.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=team.code,
            before=before,
            after=self._snapshot(team),
            actor=self.user,
        )
        return team

    @transaction.atomic
    def activate(self, code: str) -> Team:
        team = self.get(code=code)
        if not team.is_active:
            before = self._snapshot(team)
            team.is_active = True
            team.updated_by = self.user
            team.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=team.code,
                before=before,
                after=self._snapshot(team),
                actor=self.user,
            )
        return team

    @transaction.atomic
    def deactivate(self, code: str) -> Team:
        team = self.get(code=code)
        if team.is_active:
            before = self._snapshot(team)
            team.is_active = False
            team.updated_by = self.user
            team.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=team.code,
                before=before,
                after=self._snapshot(team),
                actor=self.user,
            )
        return team

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        team = self.get(code=code)
        team_code = team.code
        before = self._snapshot(team)
        team.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=team_code,
            before=before,
            actor=self.user,
        )

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_team_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    def options(self) -> list[dict]:
        return [{"code": t.code, "name": t.name} for t in selectors.get_active_teams()]


class TeamImportService(ImportService):
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
        team_svc = TeamService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            description = (row.get("description") or "").strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if selectors.team_name_exists(name):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A team named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                team_svc.create(name=name, description=description, is_active=is_active)

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class TeamExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Name",
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
    EXPORT_FILENAME = "teams_export"
    EXPORT_MODULE_NAME = "Teams"

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

        qs = selectors.get_all_teams()
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
            f"Allowed: csv, xlsx, pdf, json."
        )
