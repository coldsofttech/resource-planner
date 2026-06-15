from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.models import Project, ProjectTag
from apps.tags.models import Tag
from apps.tags.selectors import get_tag_by_code, get_tag_by_name


class ProjectTagService(AuditableService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_tag"

    def _snapshot(self, project_tag: ProjectTag) -> dict:
        return {
            "code": project_tag.code,
            "project_code": project_tag.project.code,
            "tag_code": project_tag.tag.code,
            "tag_name": project_tag.tag.name,
        }

    def _get_project(self, project_code: str) -> Project:
        obj = selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def _get_tag(self, tag_code: str) -> Tag:
        obj = get_tag_by_code(tag_code)
        if obj is None:
            raise NotFoundException(
                resource="Tag", lookup_field="code", lookup_value=tag_code
            )
        return obj

    def _get_or_create_tag(self, name: str) -> Tag:
        tag = get_tag_by_name(name)
        if tag is None:
            tag = Tag.objects.create(
                name=name.strip(), created_by=self.user, updated_by=self.user
            )
            AuditService.log_create(
                module="tags",
                resource_type="tag",
                resource_code=tag.code,
                after={"code": tag.code, "name": tag.name},
                actor=self.user,
            )
        return tag

    def get(self, code: str) -> ProjectTag:
        obj = selectors.get_project_tag_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectTag", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str) -> list[ProjectTag]:
        project = self._get_project(project_code)
        return list(selectors.get_all_project_tags(project))

    @transaction.atomic
    def create(
        self,
        *,
        project_code: str,
        tag_code: str | None = None,
        tag_name: str | None = None,
    ) -> ProjectTag:
        project = self._get_project(project_code)
        tag = (
            self._get_tag(tag_code)
            if tag_code
            else self._get_or_create_tag(tag_name or "")
        )

        if selectors.project_tag_exists(project, tag):
            raise AlreadyExistsException(
                detail=f"Tag '{tag.name}' is already assigned to this project."
            )

        obj = ProjectTag.objects.create(
            project=project,
            tag=tag,
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
    def update(self, code: str, **kwargs) -> ProjectTag:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "tag_code" in kwargs:
            new_tag = self._get_tag(kwargs["tag_code"])
            if new_tag.pk != obj.tag_id:
                already = selectors.project_tag_exists(
                    obj.project, new_tag, exclude_pk=obj.pk
                )
                if already:
                    raise AlreadyExistsException(
                        detail=(
                            f"Tag '{new_tag.name}' is already assigned to this project."
                        )
                    )
                obj.tag = new_tag
                update_fields.append("tag")

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
    def delete(self, code: str) -> None:
        obj = self.get(code=code)
        tag_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=tag_code,
            before=before,
            actor=self.user,
        )
