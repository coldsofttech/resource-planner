from __future__ import annotations

import math

from django.db import transaction

from apps.audit.services import AuditService
from apps.comments.models import Comment, CommentMention
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService
from apps.core.types import PaginatedResult, Pagination
from apps.projects import selectors
from apps.projects.models import Project, ProjectComment
from apps.users.models import User


class ProjectCommentService(AuditableService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_comment"

    def _snapshot(self, obj: ProjectComment) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "comment_code": obj.comment.code,
            "comment": obj.comment.comment,
            "is_edited": obj.comment.is_edited,
            "is_pinned": obj.comment.is_pinned,
        }

    def _get_project(self, project_code: str) -> Project:
        obj = selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def _resolve_mentioned_users(self, mention_codes: list[str]) -> list[User]:
        if not mention_codes:
            return []
        return list(
            User.objects.select_related("profile").filter(
                profile__code__in=mention_codes
            )
        )

    def _sync_mentions(self, comment: Comment, mention_codes: list[str]) -> None:
        comment.mentions.all().delete()
        users = self._resolve_mentioned_users(mention_codes)
        if users:
            CommentMention.objects.bulk_create(
                [CommentMention(comment=comment, user=user) for user in users]
            )

    def get(self, code: str) -> ProjectComment:
        obj = selectors.get_project_comment_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectComment", lookup_field="code", lookup_value=code
            )
        return obj

    def list(
        self, project_code: str, page: int = 1, page_size: int = 25
    ) -> PaginatedResult:
        project = self._get_project(project_code)
        qs = selectors.get_all_project_comments(project)
        total_count = qs.count()
        total_pages = max(1, math.ceil(total_count / page_size))
        page = max(1, min(page, total_pages))
        start = (page - 1) * page_size
        results = list(qs[start : start + page_size])
        return PaginatedResult(
            results=results,
            pagination=Pagination(
                total_count=total_count,
                total_pages=total_pages,
                current_page=page,
                page_size=page_size,
                has_next=page < total_pages,
                has_previous=page > 1,
            ),
        )

    @transaction.atomic
    def create(
        self,
        *,
        project_code: str,
        comment: str,
        mentions: list[str] | None = None,  # type: ignore[valid-type]
    ) -> ProjectComment:
        project = self._get_project(project_code)
        comment_obj = Comment.objects.create(
            comment=comment,
            created_by=self.user,
            updated_by=self.user,
        )
        if mentions:
            self._sync_mentions(comment_obj, mentions)
        obj = ProjectComment.objects.create(
            project=project,
            comment=comment_obj,
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
    def update(
        self,
        *,
        code: str,
        comment: str | None = None,
        mentions: list[str] | None = None,  # type: ignore[valid-type]
    ) -> ProjectComment:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        comment_obj = obj.comment

        if comment is not None:
            comment_obj.comment = comment
            comment_obj.is_edited = True
            comment_obj.updated_by = self.user
            comment_obj.save(
                update_fields=["comment", "is_edited", "updated_by", "updated_at"]
            )

        if mentions is not None:
            self._sync_mentions(comment_obj, mentions)

        obj.updated_by = self.user
        obj.save(update_fields=["updated_by", "updated_at"])

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
    def delete(self, *, code: str) -> None:
        obj = self.get(code=code)
        obj_code = obj.code
        before = self._snapshot(obj)
        comment_obj = obj.comment
        obj.delete()
        comment_obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )

    _MAX_PINNED = 3

    @transaction.atomic
    def pin(self, *, code: str) -> ProjectComment:
        obj = self.get(code=code)
        if not obj.comment.is_pinned:
            pinned_count = selectors.get_pinned_project_comments_count(obj.project)
            if pinned_count >= self._MAX_PINNED:
                raise ValidationException(
                    f"A project can have at most {self._MAX_PINNED} pinned comments."
                )
        before = self._snapshot(obj)
        obj.comment.is_pinned = True
        obj.comment.updated_by = self.user
        obj.comment.save(update_fields=["is_pinned", "updated_by", "updated_at"])
        obj.updated_by = self.user
        obj.save(update_fields=["updated_by", "updated_at"])
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
    def unpin(self, *, code: str) -> ProjectComment:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        obj.comment.is_pinned = False
        obj.comment.updated_by = self.user
        obj.comment.save(update_fields=["is_pinned", "updated_by", "updated_at"])
        obj.updated_by = self.user
        obj.save(update_fields=["updated_by", "updated_at"])
        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj
