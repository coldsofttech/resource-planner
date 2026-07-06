from __future__ import annotations

import logging
import mimetypes
import os

from django.db import transaction

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.projects import selectors
from apps.projects.models import Onboarding, OnboardingAttachment

logger = logging.getLogger(__name__)

_FOLDER = "onboarding_attachments"
_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def _get_onboarding(code: str) -> Onboarding:
    obj = selectors.get_onboarding_by_code(code)
    if obj is None:
        raise NotFoundException(
            resource="Onboarding", lookup_field="code", lookup_value=code
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


def _store(content: bytes, filename: str, content_type: str) -> str:
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


def _delete_file(uri: str) -> None:
    from storagecore import delete as storagecore_delete

    try:
        storagecore_delete(
            uri,
            aws_region=os.environ.get("AWS_REGION", ""),
            aws_access_key=os.environ.get("AWS_ACCESS_KEY_ID", ""),
            aws_secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        )
    except Exception:
        logger.warning("Failed to delete onboarding attachment file.")


class OnboardingAttachmentService:
    @transaction.atomic
    def upload(
        self,
        *,
        onboarding_code: str,
        file_data: bytes,
        file_name: str,
        content_type: str,
        file_size: int,
    ) -> OnboardingAttachment:
        if file_size > _MAX_FILE_SIZE:
            raise ValidationException(
                f"File exceeds the maximum allowed size of "
                f"{_MAX_FILE_SIZE // (1024 * 1024)} MB."
            )

        onboarding = _get_onboarding(onboarding_code)
        safe_name = _sanitize_filename(file_name)
        resolved_ct = _resolve_content_type(safe_name, content_type)

        if selectors.onboarding_attachment_filename_exists(onboarding, safe_name):
            raise AlreadyExistsException(
                detail=(
                    f"An attachment named '{safe_name}' already exists "
                    "for this demand request."
                )
            )

        obj = OnboardingAttachment.objects.create(
            onboarding=onboarding,
            file_name=safe_name,
            content_type=resolved_ct,
            file_size=file_size,
            file_path="",
        )

        storage_filename = f"{obj.code}_{safe_name}"
        uri = _store(file_data, storage_filename, resolved_ct)

        obj.file_path = uri
        obj.save(update_fields=["file_path"])
        return obj

    def get(self, code: str) -> OnboardingAttachment:
        obj = selectors.get_onboarding_attachment_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="OnboardingAttachment", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, onboarding_code: str) -> list[OnboardingAttachment]:
        onboarding = _get_onboarding(onboarding_code)
        return list(selectors.get_attachments_for_onboarding(onboarding))

    def download(self, code: str) -> tuple[bytes, str, str]:
        from storagecore import retrieve as storagecore_retrieve

        obj = self.get(code)
        if not obj.file_path:
            raise NotFoundException(
                resource="OnboardingAttachment",
                lookup_field="code",
                lookup_value=code,
            )
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
        uri = obj.file_path
        obj.delete()
        if uri:
            _delete_file(uri)
