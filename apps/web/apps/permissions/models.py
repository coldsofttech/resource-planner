from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import models

from apps.core.models import CodeModel, unique_constraint
from apps.permissions.constants import PermissionScope


class PermissionCategory(CodeModel):
    MODEL_CODE = "PERM"

    module = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100, db_index=True)
    label = models.CharField(max_length=200)
    permissions = models.ManyToManyField(
        Permission,
        related_name="categories",
        blank=True,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["module", "order"]
        constraints = [
            unique_constraint(
                app_label="permissions",
                model="permissioncategory",
                fields=["module", "codename"],
            ),
        ]

    def __str__(self) -> str:
        return self.label


class GroupPermissionCategory(CodeModel):
    MODEL_CODE = "GRPPERM"

    group = models.ForeignKey(
        "auth.Group",
        on_delete=models.CASCADE,
        related_name="permission_categories",
    )
    category = models.ForeignKey(
        PermissionCategory,
        on_delete=models.CASCADE,
        related_name="group_assignments",
    )
    scope = models.IntegerField(
        choices=PermissionScope.choices,
        default=PermissionScope.SELF,
        db_index=True,
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["group", "category"]
        constraints = [
            unique_constraint(
                app_label="permissions",
                model="grouppermissioncategory",
                fields=["group", "category"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.group} — {self.category} ({self.get_scope_display()})"


class UserPermissionCategory(CodeModel):
    MODEL_CODE = "USRPERM"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="permission_categories",
    )
    category = models.ForeignKey(
        PermissionCategory,
        on_delete=models.CASCADE,
        related_name="user_assignments",
    )
    scope = models.IntegerField(
        choices=PermissionScope.choices,
        default=PermissionScope.SELF,
        db_index=True,
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user", "category"]
        constraints = [
            unique_constraint(
                app_label="permissions",
                model="userpermissioncategory",
                fields=["user", "category"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.category} ({self.get_scope_display()})"
