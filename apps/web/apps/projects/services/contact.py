from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.contacts.models import Contact
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService
from apps.projects import selectors
from apps.projects.constants import ContactRole
from apps.projects.models import Project, ProjectContact


class ProjectContactService(AuditableService):
    _MODULE = "projects"
    _RESOURCE_TYPE = "project_contact"

    def _snapshot(self, obj: ProjectContact) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "contact_code": obj.contact.code,
            "contact_name": obj.contact.name,
            "contact_email": obj.contact.email,
            "role": obj.role,
        }

    def _get_project(self, project_code: str) -> Project:
        obj = selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def _find_or_create_contact(self, name: str, email: str) -> Contact:
        contact = selectors.get_contact_by_name_and_email(name, email)
        if contact is None:
            contact = Contact.objects.create(
                name=name.strip(),
                email=email.strip(),
                created_by=self.user,
                updated_by=self.user,
            )
            AuditService.log_create(
                module="contacts",
                resource_type="contact",
                resource_code=contact.code,
                after={
                    "code": contact.code,
                    "name": contact.name,
                    "email": contact.email,
                },
                actor=self.user,
            )
        return contact

    def get(self, code: str) -> ProjectContact:
        obj = selectors.get_project_contact_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectContact", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, project_code: str) -> list[ProjectContact]:
        project = self._get_project(project_code)
        return list(selectors.get_all_project_contacts(project))

    @transaction.atomic
    def create(
        self,
        *,
        project_code: str,
        name: str,
        email: str,
        role: str,
    ) -> ProjectContact:
        project = self._get_project(project_code)

        if role not in ContactRole.values:
            raise ValueError(f"Invalid role '{role}'.")

        contact = self._find_or_create_contact(name, email)

        if selectors.project_contact_exists(project, contact):
            raise AlreadyExistsException(
                detail=f"Contact '{contact.name}' is already assigned to this project."
            )

        obj = ProjectContact.objects.create(
            project=project,
            contact=contact,
            role=role,
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
    def delete(self, code: str) -> None:
        obj = self.get(code=code)
        obj_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )
