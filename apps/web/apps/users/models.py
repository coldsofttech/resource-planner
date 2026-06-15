from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import ActivatableModel, AuditableModel, CodeModel
from apps.users.constants import ThemeChoices

User = get_user_model()

GROUP_ADMINISTRATORS = "Administrators"
GROUP_GUESTS = "Guests"


class UserProfile(AuditableModel, CodeModel):
    MODEL_CODE = "USER"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

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

    # User preferences.
    theme = models.CharField(
        max_length=10,
        choices=ThemeChoices.choices,
        default=ThemeChoices.LIGHT,
    )
    timezone = models.CharField(max_length=100, default="UTC", blank=True)

    # Auto-populated as "lastname, firstname" on creation; user-overridable.
    display_name = models.CharField(max_length=150, blank=True)

    # Workforce fields — updatable only by users with change_user_workforce permission.
    location = models.ForeignKey(
        "locations.Location",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
    )
    employment_type = models.ForeignKey(
        "employment_types.EmploymentType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
    )
    role = models.ForeignKey(
        "roles.Role",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
    )

    # Skills — user-updatable; constrained to active skills at the service/API layer.
    skills = models.ManyToManyField(
        "skills.Skill",
        blank=True,
        related_name="user_profiles",
    )

    # Workforce dates and capacity — managed via the Members page.
    joined_date = models.DateField(null=True, blank=True)
    leaving_date = models.DateField(null=True, blank=True)
    default_holidays = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["user"]
        permissions = [
            ("change_user_workforce", "Can change user workforce details"),
            ("export_member", "Can export members"),
        ]


class UserAvatar(AuditableModel):
    """
    Stores a user's active avatar URI.  The avatar field holds one of:
      data:<mime>;base64,<b64>                           — database backend
      file:<absolute-path>                               — filesystem backend
      aws:arn:aws:s3:::<bucket>/<folder>/<filename>      — S3 backend
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="avatars",
    )
    avatar = models.TextField()

    class Meta:
        ordering = ["-created_at"]


class GroupProfile(ActivatableModel, AuditableModel, CodeModel):
    MODEL_CODE = "USRGRP"

    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="profile"
    )
    description = models.CharField(blank=True)
    is_admin_group = models.BooleanField(default=False, db_index=True)
    is_system = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["group"]
        permissions = [
            ("view_group", "Can view groups"),
            ("add_group", "Can add groups"),
            ("change_group", "Can change groups"),
            ("delete_group", "Can delete groups"),
            ("import_group", "Can import groups"),
            ("export_group", "Can export groups"),
        ]

    def __str__(self):
        return self.group.name
