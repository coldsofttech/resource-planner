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
from apps.skills import selectors
from apps.skills.models import Skill


class SkillService(AuditableService, FilterableQueryService):
    _MODULE = "skills"
    _RESOURCE_TYPE = "skill"

    filterable_fields: dict[str, str] = {}
    search_fields: list[str] = ["skill"]
    sortable_fields: list[str] = ["skill", "is_active", "created_at"]
    default_ordering: list[str] = ["skill"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_skills()

    def _snapshot(self, skill_obj: Skill) -> dict:
        return {
            "code": skill_obj.code,
            "skill": skill_obj.skill,
            "description": skill_obj.description,
            "is_active": skill_obj.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> Skill:
        obj = selectors.get_skill_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Skill", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self, *, skill: str, is_active: bool = True, description: str = ""
    ) -> Skill:
        if selectors.skill_exists(skill):
            raise AlreadyExistsException(
                detail=f"A skill named '{skill}' already exists."
            )
        skill_obj = Skill.objects.create(
            skill=skill,
            description=description,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=skill_obj.code,
            after=self._snapshot(skill_obj),
            actor=self.user,
        )
        return skill_obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Skill:
        skill_obj = self.get(code=code)
        before = self._snapshot(skill_obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "skill" in kwargs:
            new_skill = kwargs["skill"]
            if new_skill != skill_obj.skill and selectors.skill_exists(
                new_skill, exclude_pk=skill_obj.pk
            ):
                raise AlreadyExistsException(
                    detail=f"A skill named '{new_skill}' already exists."
                )
            skill_obj.skill = new_skill
            update_fields.append("skill")

        if "description" in kwargs:
            skill_obj.description = kwargs["description"]
            update_fields.append("description")

        if "is_active" in kwargs:
            skill_obj.is_active = kwargs["is_active"]
            update_fields.append("is_active")

        skill_obj.updated_by = self.user
        skill_obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=skill_obj.code,
            before=before,
            after=self._snapshot(skill_obj),
            actor=self.user,
        )
        return skill_obj

    @transaction.atomic
    def activate(self, code: str) -> Skill:
        skill_obj = self.get(code=code)
        if not skill_obj.is_active:
            before = self._snapshot(skill_obj)
            skill_obj.is_active = True
            skill_obj.updated_by = self.user
            skill_obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=skill_obj.code,
                before=before,
                after=self._snapshot(skill_obj),
                actor=self.user,
            )
        return skill_obj

    @transaction.atomic
    def deactivate(self, code: str) -> Skill:
        skill_obj = self.get(code=code)
        if skill_obj.is_active:
            before = self._snapshot(skill_obj)
            skill_obj.is_active = False
            skill_obj.updated_by = self.user
            skill_obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=skill_obj.code,
                before=before,
                after=self._snapshot(skill_obj),
                actor=self.user,
            )
        return skill_obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        skill_obj = self.get(code=code)
        skill_code = skill_obj.code
        before = self._snapshot(skill_obj)
        skill_obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=skill_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {"code": s.code, "skill": s.skill} for s in selectors.get_skill_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_skill_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats


class SkillImportService(ImportService):
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
        skill = (row.get("skill") or "").strip()
        if not skill:
            errors.append(
                {"row": row_num, "field": "skill", "message": "Skill is required."}
            )
        elif len(skill) > 20:
            errors.append(
                {
                    "row": row_num,
                    "field": "skill",
                    "message": "Skill must be 20 characters or fewer.",
                }
            )
        return errors

    def bulk_import(self, file, dry_run: bool = False) -> dict:
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        required_columns = {"skill"}
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
        skill_svc = SkillService(user=self.user)

        for row_num, row in enumerate(rows, start=2):
            row_errors = self.validate_row(row, row_num)
            if row_errors:
                errors.extend(row_errors)
                continue

            skill = row["skill"].strip()
            description = (row.get("description") or "").strip()
            is_active_raw = (row.get("is_active") or "true").strip().lower()
            is_active = is_active_raw not in ("false", "0", "no")

            if selectors.skill_exists(skill):
                errors.append(
                    {
                        "row": row_num,
                        "field": "skill",
                        "message": f"A skill named '{skill}' already exists.",
                    }
                )
                continue

            if not dry_run:
                skill_svc.create(
                    skill=skill, description=description, is_active=is_active
                )

            created_rows.append({"row": row_num, "field": "skill", "message": skill})

        return {
            "total": total,
            "created_rows": created_rows,
            "errors": errors,
            "dry_run": dry_run,
        }


class SkillExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "skill": "Skill",
        "description": "Description",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "skill",
        "description",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "skills_export"
    EXPORT_MODULE_NAME = "Skills"

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

        qs = selectors.get_all_skills()
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
                qs = qs.filter(skill__icontains=search)

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
