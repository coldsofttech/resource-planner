from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.engine import ProjectLabelEngine
from apps.projects.models import Project, ProjectLabel


class ProjectLabelService(AuditableService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_label"

    def _snapshot(self, label: ProjectLabel) -> dict:
        return {
            "code": label.code,
            "project_code": label.project.code,
            "label": label.label,
            "is_default": label.is_default,
        }

    def _get_project(self, project_code: str) -> Project:
        obj = selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def get(self, code: str) -> ProjectLabel:
        obj = selectors.get_project_label_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectLabel", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str) -> list[ProjectLabel]:
        project = self._get_project(project_code)
        return list(selectors.get_all_project_labels(project))

    def suggest(self, project_code: str) -> str:
        project = self._get_project(project_code)
        return ProjectLabelEngine.suggest(project)

    def _demote_current_default(
        self, project: Project, exclude_pk: int | None = None
    ) -> None:
        qs = ProjectLabel.objects.filter(project=project, is_default=True)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        qs.update(is_default=False)

    @transaction.atomic
    def create(
        self,
        *,
        project_code: str,
        label: str,
        is_default: bool = False,
    ) -> ProjectLabel:
        project = self._get_project(project_code)

        if selectors.project_label_exists(project, label):
            raise AlreadyExistsException(
                detail=f"Label '{label}' already exists for this project."
            )

        if is_default:
            self._demote_current_default(project)

        obj = ProjectLabel.objects.create(
            project=project,
            label=label,
            is_default=is_default,
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
    def update(self, code: str, **kwargs) -> ProjectLabel:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "label" in kwargs:
            new_label = kwargs["label"]
            if new_label != obj.label and selectors.project_label_exists(
                obj.project, new_label, exclude_pk=obj.pk
            ):
                raise AlreadyExistsException(
                    detail=f"Label '{new_label}' already exists for this project."
                )
            obj.label = new_label
            update_fields.append("label")

        if "is_default" in kwargs:
            new_default = kwargs["is_default"]
            if new_default and not obj.is_default:
                self._demote_current_default(obj.project, exclude_pk=obj.pk)
            obj.is_default = new_default
            update_fields.append("is_default")

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
    def set_default(self, code: str) -> ProjectLabel:
        obj = self.get(code=code)
        if not obj.is_default:
            before = self._snapshot(obj)
            self._demote_current_default(obj.project, exclude_pk=obj.pk)
            obj.is_default = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_default", "updated_by", "updated_at"])
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
    def delete(self, code: str) -> None:
        obj = self.get(code=code)
        label_code = obj.code
        project = obj.project
        was_default = obj.is_default
        before = self._snapshot(obj)
        obj.delete()
        if was_default:
            ProjectLabel.objects.filter(project=project, is_default=True).update(
                is_default=False
            )
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=label_code,
            before=before,
            actor=self.user,
        )
