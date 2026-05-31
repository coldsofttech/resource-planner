from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import AuditableModel, CodeModel

User = get_user_model()

GROUP_ADMINISTRATORS = "Administrators"
GROUP_GUESTS = "Guests"


class UserProfile(AuditableModel, CodeModel):
    MODEL_CODE = "USER"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    # SSO provider — points to either an OAuth or SAML instance.
    sso_provider_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    sso_provider_object_id = models.PositiveIntegerField(null=True, blank=True)
    sso_provider = GenericForeignKey(
        "sso_provider_content_type", "sso_provider_object_id"
    )

    # Unique identifier for the user as returned by the SSO provider (sub / NameID).
    sso_uid = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # Classic-auth password management fields.
    must_change_password = models.BooleanField(default=False)
    password_last_changed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["user"]


class GroupProfile(AuditableModel, CodeModel):
    MODEL_CODE = "USRGRP"

    group = models.OneToOneField(
        "auth.Group",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    description = models.CharField(blank=True)
    is_admin_group = models.BooleanField(default=False, db_index=True)
    is_system = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["group"]

    def __str__(self):
        return self.group.name
