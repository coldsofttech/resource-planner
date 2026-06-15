from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.models import Project, ProjectFollower


class ProjectFollowerService(AuditableService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_follower"

    def _snapshot(self, follower: ProjectFollower) -> dict:
        return {
            "code": follower.code,
            "project_code": follower.project.code,
            "user_email": follower.user.email,
        }

    def _get_project(self, project_code: str) -> Project:
        obj = selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def _get_user(self, user_code: str):
        from apps.users.selectors import get_user_by_profile_code

        profile = get_user_by_profile_code(user_code)
        if profile is None:
            raise NotFoundException(
                resource="User", lookup_field="code", lookup_value=user_code
            )
        return profile.user

    def get(self, code: str) -> ProjectFollower:
        obj = selectors.get_project_follower_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectFollower", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str) -> list[ProjectFollower]:
        project = self._get_project(project_code)
        return list(selectors.get_all_project_followers(project))

    @transaction.atomic
    def create(self, *, project_code: str, user_code: str) -> ProjectFollower:
        project = self._get_project(project_code)
        user = self._get_user(user_code)

        if selectors.project_follower_exists(project, user):
            raise AlreadyExistsException(
                detail=f"User '{user.email}' is already following this project."
            )

        obj = ProjectFollower.objects.create(
            project=project,
            user=user,
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
    def update(self, code: str, **kwargs) -> ProjectFollower:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "user_code" in kwargs:
            new_user = self._get_user(kwargs["user_code"])
            if new_user.pk != obj.user_id:
                if selectors.project_follower_exists(
                    obj.project, new_user, exclude_pk=obj.pk
                ):
                    raise AlreadyExistsException(
                        detail=(
                            f"User '{new_user.email}' is already following "
                            "this project."
                        )
                    )
                obj.user = new_user
                update_fields.append("user")

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
        follower_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=follower_code,
            before=before,
            actor=self.user,
        )
