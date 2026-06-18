from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.models import Project, ProjectLink

_MODULE = "projects"
_RESOURCE_TYPE = "project_link"


def _get_project(project_code: str) -> Project:
    obj = selectors.get_project_by_code(project_code)
    if obj is None:
        raise NotFoundException(
            resource="Project", lookup_field="code", lookup_value=project_code
        )
    return obj


class ProjectLinkService(AuditableService):
    _MODULE = _MODULE
    _RESOURCE_TYPE = _RESOURCE_TYPE

    def _snapshot(self, obj: ProjectLink) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "title": obj.title,
            "url": obj.url,
        }

    def get(self, code: str) -> ProjectLink:
        obj = selectors.get_link_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectLink", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str) -> list[ProjectLink]:
        project = _get_project(project_code)
        return list(selectors.get_links_for_project(project))

    @transaction.atomic
    def create(self, *, project_code: str, title: str, url: str) -> ProjectLink:
        project = _get_project(project_code)

        if selectors.project_link_title_exists(project, title):
            raise AlreadyExistsException(
                detail=f"A link titled '{title}' already exists for this project."
            )

        obj = ProjectLink.objects.create(
            project=project,
            title=title,
            url=url,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> ProjectLink:
        obj = self.get(code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "title" in kwargs:
            new_title = kwargs["title"]
            if new_title != obj.title and selectors.project_link_title_exists(
                obj.project, new_title, exclude_pk=obj.pk
            ):
                raise AlreadyExistsException(
                    detail=(
                        f"A link titled '{new_title}' already exists for this project."
                    )
                )
            obj.title = new_title
            update_fields.append("title")

        if "url" in kwargs:
            obj.url = kwargs["url"]
            update_fields.append("url")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str) -> None:
        obj = self.get(code)
        obj_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )
