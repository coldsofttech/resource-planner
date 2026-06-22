from __future__ import annotations

import logging
import mimetypes
import os

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.models import Project, ProjectAttachment

logger = logging.getLogger(__name__)

_MODULE = "projects"
_RESOURCE_TYPE = "project_attachment"
_FOLDER = "project_attachments"
_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
_SORTABLE = frozenset({"file_name", "file_size", "content_type", "created_at"})
_DEFAULT_ORDER = ["-created_at"]


def _get_project(project_code: str) -> Project:
    obj = selectors.get_project_by_code(project_code)
    if obj is None:
        raise NotFoundException(
            resource="Project", lookup_field="code", lookup_value=project_code
        )
    return obj


def _sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename).strip()
    return name or "attachment"


def _resolve_content_type(filename: str, supplied: str) -> str:
    if supplied:
        return supplied
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


class ProjectAttachmentService(AuditableService):
    _MODULE = _MODULE
    _RESOURCE_TYPE = _RESOURCE_TYPE

    def _snapshot(self, obj: ProjectAttachment) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "file_name": obj.file_name,
            "content_type": obj.content_type,
            "file_size": obj.file_size,
        }

    def _store(self, content: bytes, filename: str, content_type: str) -> str:
        from storagecore import store as storagecore_store

        from apps.configurations.selectors import Infra

        storage_type = Infra.get_storage_type().value
        try:
            storage_path = Infra.get_storage_path()
        except Exception:
            storage_path = ""

        return storagecore_store(
            content=content,
            filename=filename,
            folder=_FOLDER,
            storage_type=storage_type,
            storage_path=storage_path,
            aws_region=os.environ.get("AWS_REGION", ""),
            aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
            aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            content_type=content_type,
        )

    def _delete_file(self, uri: str) -> None:
        from storagecore import delete as storagecore_delete

        try:
            storagecore_delete(
                uri,
                aws_region=os.environ.get("AWS_REGION", ""),
                aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
                aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
            )
        except Exception:
            logger.warning("Failed to delete attachment file.")

    def get(self, code: str) -> ProjectAttachment:
        obj = selectors.get_attachment_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectAttachment", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str, params=None) -> list[ProjectAttachment]:
        project = _get_project(project_code)
        qs = selectors.get_attachments_for_project(project)
        if params and params.sorts:
            order_fields = [
                f"-{s.sort_by}" if s.direction == "desc" else s.sort_by
                for s in params.sorts
                if s.sort_by in _SORTABLE
            ]
            if order_fields:
                qs = qs.order_by(*order_fields)
        return list(qs)

    @transaction.atomic
    def upload(
        self,
        *,
        project_code: str,
        file_data: bytes,
        file_name: str,
        content_type: str,
        file_size: int,
    ) -> ProjectAttachment:
        if file_size > _MAX_FILE_SIZE:
            raise ValidationException(
                f"File exceeds the maximum allowed size of "
                f"{_MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        project = _get_project(project_code)
        safe_name = _sanitize_filename(file_name)
        resolved_ct = _resolve_content_type(safe_name, content_type)

        if selectors.project_attachment_filename_exists(project, safe_name):
            raise AlreadyExistsException(
                detail=(
                    f"An attachment named '{safe_name}' already exists "
                    "for this project."
                )
            )

        obj = ProjectAttachment.objects.create(
            project=project,
            file_name=safe_name,
            content_type=resolved_ct,
            file_size=file_size,
            file_path="",
            created_by=self.user,
            updated_by=self.user,
        )

        storage_filename = f"{obj.code}_{safe_name}"
        uri = self._store(file_data, storage_filename, resolved_ct)

        obj.file_path = uri
        obj.save(update_fields=["file_path"])

        AuditService.log_create(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    def download(self, code: str) -> tuple[bytes, str, str]:
        from storagecore import retrieve as storagecore_retrieve

        obj = self.get(code)
        content = storagecore_retrieve(
            obj.file_path,
            aws_region=os.environ.get("AWS_REGION", ""),
            aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
            aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        )
        return content, obj.content_type or "application/octet-stream", obj.file_name

    @transaction.atomic
    def delete(self, code: str) -> None:
        obj = self.get(code)
        obj_code = obj.code
        before = self._snapshot(obj)
        uri = obj.file_path
        obj.delete()
        self._delete_file(uri)
        AuditService.log_delete(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )
