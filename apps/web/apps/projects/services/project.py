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
from apps.projects import selectors
from apps.projects.constants import Confidence, Priority
from apps.projects.models import (
    Programme,
    Project,
    ProjectCode,
    ProjectCollaborator,
    ProjectStatus,
    ProjectStatusHistory,
    ProjectSubStatus,
    ProjectType,
)
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint
from apps.teams.models import Team


class ProjectService(AuditableService, FilterableQueryService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project"

    filterable_fields: dict[str, str] = {
        "project_type": "project_type__code",
        "programme": "programme__code",
        "status": "status__code",
        "assigned_team": "assigned_team__code",
    }
    search_fields: list[str] = ["name", "display_name", "description"]
    sortable_fields: list[str] = [
        "name",
        "status__name",
        "start_date",
        "end_date",
        "created_at",
    ]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_projects()

    def _snapshot(self, project: Project) -> dict:
        return {
            "code": project.code,
            "name": project.name,
            "display_name": project.display_name,
            "description": project.description,
            "is_active": project.is_active,
            "project_type_code": project.project_type_id and project.project_type.code,
            "programme_code": project.programme_id and project.programme.code,
            "status_code": project.status_id and project.status.code,
            "sub_status_code": project.sub_status_id and project.sub_status.code,
            "assigned_team_code": project.assigned_team_id
            and project.assigned_team.code,
            "confidence": project.confidence,
            "priority": project.priority,
            "start_date": str(project.start_date) if project.start_date else None,
            "end_date": str(project.end_date) if project.end_date else None,
            "commitment_date": str(project.commitment_date)
            if project.commitment_date
            else None,
            "efforts_issued": project.efforts_issued,
            "run_cost_applies": project.run_cost_applies,
            "sprint_started_in_code": project.sprint_started_in_id
            and project.sprint_started_in.code,
            "sprint_completed_in_code": project.sprint_completed_in_id
            and project.sprint_completed_in.code,
        }

    def get(self, code: str, *args, **kwargs) -> Project:
        obj = selectors.get_project_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=code
            )
        return obj

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_project_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats

    def options(self, programme_code: str | None = None) -> list[dict]:
        return [
            {"code": p.code, "name": p.name, "display_name": p.display_name}
            for p in selectors.get_project_options(programme_code=programme_code)
        ]

    def confidence_options(self) -> list[dict]:
        return [{"code": value, "name": label} for value, label in Confidence.choices]

    def priority_options(self) -> list[dict]:
        return [{"code": value, "name": label} for value, label in Priority.choices]

    def _resolve_programme(self, programme_code: str | None) -> Programme | None:
        """Resolve a Programme by code, defaulting to the protected 'Others' record."""
        if programme_code:
            prog = selectors.get_programme_by_code(programme_code)
            if prog is None:
                raise NotFoundException(
                    resource="Programme",
                    lookup_field="code",
                    lookup_value=programme_code,
                )
            return prog
        return Programme.objects.filter(name="Others", is_protected=True).first()

    def _resolve_project_type(self, code: str) -> ProjectType:
        obj = selectors.get_project_type_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectType", lookup_field="code", lookup_value=code
            )
        return obj

    def _resolve_status(self, code: str) -> ProjectStatus:
        obj = selectors.get_project_status_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectStatus", lookup_field="code", lookup_value=code
            )
        return obj

    def _resolve_sub_status(self, code: str | None) -> ProjectSubStatus | None:
        if not code:
            return None
        obj = selectors.get_project_sub_status_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectSubStatus", lookup_field="code", lookup_value=code
            )
        return obj

    def _resolve_team(self, code: str | None) -> Team | None:
        if not code:
            return None
        try:
            return Team.objects.get(code=code)
        except Team.DoesNotExist as exc:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=code
            ) from exc

    def _resolve_sprint(self, code: str | None) -> Sprint | None:
        if not code:
            return None
        obj = sprint_selectors.get_sprint_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=code
            )
        return obj

    def _record_status_history(
        self,
        project: Project,
        previous_status: ProjectStatus | None,
        new_status: ProjectStatus | None,
        previous_sub_status: ProjectSubStatus | None,
        new_sub_status: ProjectSubStatus | None,
        note: str = "",
    ) -> None:
        ProjectStatusHistory.objects.create(
            project=project,
            previous_status=previous_status,
            new_status=new_status,
            previous_sub_status=previous_sub_status,
            new_sub_status=new_sub_status,
            note=note,
            changed_by=self.user,
        )

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        project_type_code: str,
        status_code: str,
        programme_code: str | None = None,
        sub_status_code: str | None = None,
        assigned_team_code: str | None = None,
        description: str = "",
        is_active: bool = True,
        confidence: str | None = None,
        priority: str | None = None,
        start_date=None,
        end_date=None,
        commitment_date=None,
        efforts_issued: bool = False,
        run_cost_applies: bool = False,
        sprint_started_in_code: str | None = None,
        sprint_completed_in_code: str | None = None,
    ) -> Project:
        if selectors.project_name_exists(name):
            raise AlreadyExistsException(
                detail=f"A project named '{name}' already exists."
            )

        project_type = self._resolve_project_type(project_type_code)
        programme = self._resolve_programme(programme_code)
        status = self._resolve_status(status_code)
        sub_status = self._resolve_sub_status(sub_status_code)
        assigned_team = self._resolve_team(assigned_team_code)
        sprint_started_in = self._resolve_sprint(sprint_started_in_code)
        sprint_completed_in = self._resolve_sprint(sprint_completed_in_code)

        obj = Project.objects.create(
            name=name,
            display_name=name,
            description=description,
            is_active=is_active,
            project_type=project_type,
            programme=programme,
            status=status,
            sub_status=sub_status,
            assigned_team=assigned_team,
            confidence=confidence,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            commitment_date=commitment_date,
            efforts_issued=efforts_issued,
            run_cost_applies=run_cost_applies,
            sprint_started_in=sprint_started_in,
            sprint_completed_in=sprint_completed_in,
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
        self._record_status_history(
            project=obj,
            previous_status=None,
            new_status=status,
            previous_sub_status=None,
            new_sub_status=sub_status,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Project:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at", "display_name"]

        previous_status = obj.status
        previous_sub_status = obj.sub_status

        new_name = kwargs.get("name", obj.name)
        if new_name != obj.name and selectors.project_name_exists(
            new_name, exclude_pk=obj.pk
        ):
            raise AlreadyExistsException(
                detail=f"A project named '{new_name}' already exists."
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

        if "project_type_code" in kwargs:
            obj.project_type = self._resolve_project_type(kwargs["project_type_code"])
            update_fields.append("project_type")

        if "programme_code" in kwargs:
            obj.programme = self._resolve_programme(kwargs["programme_code"])
            update_fields.append("programme")

        if "status_code" in kwargs:
            obj.status = self._resolve_status(kwargs["status_code"])
            update_fields.append("status")

        if "sub_status_code" in kwargs:
            obj.sub_status = self._resolve_sub_status(kwargs["sub_status_code"])
            update_fields.append("sub_status")

        if "assigned_team_code" in kwargs:
            obj.assigned_team = self._resolve_team(kwargs["assigned_team_code"])
            update_fields.append("assigned_team")

        for field in (
            "confidence",
            "priority",
            "start_date",
            "end_date",
            "commitment_date",
            "efforts_issued",
            "run_cost_applies",
        ):
            if field in kwargs:
                setattr(obj, field, kwargs[field])
                update_fields.append(field)

        if "sprint_started_in_code" in kwargs:
            obj.sprint_started_in = self._resolve_sprint(
                kwargs["sprint_started_in_code"]
            )
            update_fields.append("sprint_started_in")

        if "sprint_completed_in_code" in kwargs:
            obj.sprint_completed_in = self._resolve_sprint(
                kwargs["sprint_completed_in_code"]
            )
            update_fields.append("sprint_completed_in")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        if "project_code_value" in kwargs:
            new_value = (kwargs["project_code_value"] or "").strip()
            if new_value:
                existing = obj.codes.first()
                if existing is None:
                    ProjectCode.objects.create(
                        project=obj,
                        value=new_value,
                        created_by=self.user,
                        updated_by=self.user,
                    )
                elif existing.value != new_value:
                    existing.value = new_value
                    existing.updated_by = self.user
                    existing.save(update_fields=["value", "updated_by"])

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )

        status_changed = (
            obj.status_id != previous_status.pk
            if previous_status
            else obj.status_id is not None
        )
        sub_status_changed = obj.sub_status_id != (
            previous_sub_status.pk if previous_sub_status else None
        )
        if status_changed or sub_status_changed:
            self._record_status_history(
                project=obj,
                previous_status=previous_status,
                new_status=obj.status,
                previous_sub_status=previous_sub_status,
                new_sub_status=obj.sub_status,
                note=kwargs.get("status_note", ""),
            )

        return obj

    @transaction.atomic
    def activate(self, code: str) -> Project:
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
    def deactivate(self, code: str) -> Project:
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
        project_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=project_code,
            before=before,
            actor=self.user,
        )

    @transaction.atomic
    def add_collaborator(
        self, project_code: str, team_code: str
    ) -> ProjectCollaborator:
        project = self.get(code=project_code)
        team = self._resolve_team(team_code)

        if project.assigned_team_id and team is not None:
            if project.assigned_team.code == team_code:
                raise ValidationException(
                    "The collaborating team cannot be the same as the assigned team."
                )

        existing = selectors.get_project_collaborator(project, team_code)
        if existing is not None:
            raise AlreadyExistsException(
                detail=f"Team '{team_code}' is already a collaborator on this project."
            )

        collaborator = ProjectCollaborator.objects.create(
            project=project,
            team=team,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type="project_collaborator",
            resource_code=f"{project_code}:{team_code}",
            after={"project_code": project_code, "team_code": team_code},
            actor=self.user,
        )
        return collaborator

    @transaction.atomic
    def remove_collaborator(self, project_code: str, team_code: str) -> None:
        project = self.get(code=project_code)
        collaborator = selectors.get_project_collaborator(project, team_code)
        if collaborator is None:
            raise NotFoundException(
                resource="ProjectCollaborator",
                lookup_field="team_code",
                lookup_value=team_code,
            )
        collaborator.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type="project_collaborator",
            resource_code=f"{project_code}:{team_code}",
            before={"project_code": project_code, "team_code": team_code},
            actor=self.user,
        )


class ProjectImportService(ImportService):
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
                    "message": "Project name is required.",
                }
            )
        elif len(name) > 255:
            errors.append(
                {
                    "row": row_num,
                    "field": "name",
                    "message": "Project name must be 255 characters or fewer.",
                }
            )
        if not (row.get("project_type_code") or "").strip():
            errors.append(
                {
                    "row": row_num,
                    "field": "project_type_code",
                    "message": "Project type code is required.",
                }
            )
        if not (row.get("status_code") or "").strip():
            errors.append(
                {
                    "row": row_num,
                    "field": "status_code",
                    "message": "Status code is required.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"name", "project_type_code", "status_code"}
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
        svc = ProjectService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            name = row["name"].strip()
            project_type_code = row["project_type_code"].strip()
            status_code = row["status_code"].strip()
            programme_code = (row.get("programme_code") or "").strip() or None
            description = (row.get("description") or "").strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if selectors.project_name_exists(name):
                errors.append(
                    {
                        "row": row_num,
                        "field": "name",
                        "message": f"A project named '{name}' already exists.",
                    }
                )
                continue

            if not dry_run:
                try:
                    svc.create(
                        name=name,
                        project_type_code=project_type_code,
                        status_code=status_code,
                        programme_code=programme_code,
                        description=description,
                        is_active=is_active,
                    )
                except (NotFoundException, ValidationException) as exc:
                    errors.append(
                        {
                            "row": row_num,
                            "field": "general",
                            "message": str(exc),
                        }
                    )
                    continue

            created_rows.append({"row": row_num, "field": "name", "message": name})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class ProjectExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "name": "Project Name",
        "display_name": "Display Name",
        "description": "Description",
        "project_type": "Project Type",
        "programme": "Programme",
        "status": "Status",
        "sub_status": "Sub Status",
        "assigned_team": "Assigned Team",
        "confidence": "Confidence",
        "priority": "Priority",
        "start_date": "Start Date",
        "end_date": "End Date",
        "commitment_date": "Commitment Date",
        "efforts_issued": "Efforts/Issues",
        "run_cost_applies": "Run Cost Applies",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "name",
        "display_name",
        "project_type",
        "programme",
        "status",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "projects_export"
    EXPORT_MODULE_NAME = "Projects"

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

        qs = selectors.get_all_projects()
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
