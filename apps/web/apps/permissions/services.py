from __future__ import annotations

from typing import List

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import ContextService, FilterableQueryService, paginate_queryset
from apps.core.types import ListParams
from apps.permissions import selectors
from apps.permissions.models import GroupPermissionCategory, UserPermissionCategory


class PermissionCategoryService(FilterableQueryService):
    filterable_fields = {
        "module": "module",
    }
    search_fields = ["name", "label", "codename"]
    sortable_fields = ["module", "order", "name", "codename"]
    default_ordering = ["module", "order"]

    def get_queryset(self):
        return selectors.get_all_categories()

    def get(self, pk: str, *args, **kwargs):
        obj = selectors.get_category_by_code(pk)
        if obj is None:
            raise NotFoundException(
                resource="Permission Category",
                lookup_field="code",
                lookup_value=pk,
            )
        return obj


class GroupPermissionCategoryService(ContextService):
    def _resolve_group(self, group_code: str):
        group = selectors.get_group_by_profile_code(group_code)
        if group is None:
            raise NotFoundException(
                resource="Group",
                lookup_field="code",
                lookup_value=group_code,
            )
        return group

    def _resolve_assignment(self, group_code: str, code: str):
        group = self._resolve_group(group_code)
        assignment = selectors.get_group_assignment_by_code(code)
        if assignment is None or assignment.group_id != group.pk:
            raise NotFoundException(
                resource="Group assignment",
                lookup_field="code",
                lookup_value=code,
            )
        return assignment

    def list(self, *, group_code: str, params: ListParams):
        group = self._resolve_group(group_code)
        qs = selectors.get_group_categories(group)
        return paginate_queryset(qs, params.page, params.page_size)

    def assign(
        self, *, group_code: str, category_code: str, scope: int
    ) -> GroupPermissionCategory:
        group = self._resolve_group(group_code)
        category = selectors.get_category_by_code(category_code)
        if category is None:
            raise NotFoundException(
                resource="Permission Category",
                lookup_field="code",
                lookup_value=category_code,
            )
        if GroupPermissionCategory.objects.filter(
            group=group, category=category
        ).exists():
            raise AlreadyExistsException(
                detail="This category is already assigned to the group."
            )
        return GroupPermissionCategory.objects.create(
            group=group, category=category, scope=scope
        )

    def update_scope(
        self, *, group_code: str, code: str, scope: int
    ) -> GroupPermissionCategory:
        assignment = self._resolve_assignment(group_code, code)
        assignment.scope = scope
        assignment.save(update_fields=["scope"])
        return assignment

    def remove(self, *, group_code: str, code: str) -> None:
        assignment = self._resolve_assignment(group_code, code)
        assignment.delete()


class UserPermissionCategoryService(ContextService):
    def _resolve_user(self, user_code: str):
        user = selectors.get_user_by_profile_code(user_code)
        if user is None:
            raise NotFoundException(
                resource="User",
                lookup_field="code",
                lookup_value=user_code,
            )
        return user

    def _resolve_assignment(self, user_code: str, code: str):
        user = self._resolve_user(user_code)
        assignment = selectors.get_user_assignment_by_code(code)
        if assignment is None or assignment.user_id != user.pk:
            raise NotFoundException(
                resource="User assignment",
                lookup_field="code",
                lookup_value=code,
            )
        return assignment

    def list(self, *, user_code: str, params: ListParams):
        user = self._resolve_user(user_code)
        qs = selectors.get_user_categories(user)
        return paginate_queryset(qs, params.page, params.page_size)

    def assign(
        self, *, user_code: str, category_code: str, scope: int
    ) -> UserPermissionCategory:
        user = self._resolve_user(user_code)
        category = selectors.get_category_by_code(category_code)
        if category is None:
            raise NotFoundException(
                resource="Permission Category",
                lookup_field="code",
                lookup_value=category_code,
            )
        if UserPermissionCategory.objects.filter(user=user, category=category).exists():
            raise AlreadyExistsException(
                detail="This category is already assigned to the user."
            )
        return UserPermissionCategory.objects.create(
            user=user, category=category, scope=scope
        )

    def update_scope(
        self, *, user_code: str, code: str, scope: int
    ) -> UserPermissionCategory:
        assignment = self._resolve_assignment(user_code, code)
        assignment.scope = scope
        assignment.save(update_fields=["scope"])
        return assignment

    def remove(self, *, user_code: str, code: str) -> None:
        assignment = self._resolve_assignment(user_code, code)
        assignment.delete()

    def effective(self, *, user_code: str) -> List[dict]:
        user = self._resolve_user(user_code)
        return selectors.get_effective_user_assignments(user)
