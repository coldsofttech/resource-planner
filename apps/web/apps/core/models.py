from django.conf import settings
from django.db import models
from django.db.models import Q

MAX_CONSTRAINT_NAME_LENGTH = 63


def build_constraint_name(*parts: str) -> str:
    """
    Builds deterministic constraint names under backend length limits.
    Postgres enforces 63-character identifier limit.
    SQLite is typically more permissive.
    We keep names portable by enforcing the lower limit.
    """
    clean_parts = [part.strip().lower() for part in parts if part and part.strip()]
    joined = "_".join(clean_parts)

    if len(joined) <= MAX_CONSTRAINT_NAME_LENGTH:
        return joined

    import hashlib

    digest = hashlib.md5(joined.encode()).hexdigest()[:8]  # nosec B324
    truncated = joined[:50]
    return f"{truncated}_{digest}"


def unique_constraint(
    *, app_label: str, model: str, fields: list[str]
) -> models.UniqueConstraint:
    """Create a consistently-named multi-column unique constraint."""
    name = build_constraint_name(app_label, model, *fields, "uniq")
    return models.UniqueConstraint(fields=fields, name=name)


def check_constraint(
    *, app_label: str, model: str, suffix: str, condition: Q
) -> models.CheckConstraint:
    """Create a consistently-named check constraint."""
    name = build_constraint_name(app_label, model, suffix, "chk")
    return models.CheckConstraint(condition=condition, name=name)


class BaseModel(models.Model):
    """Base model"""

    class Meta:
        abstract = True


class CodeModel(models.Model):
    """Base model with code field. Examples: SUB-1, CONFIG-2, etc."""

    MODEL_CODE = "BASE"

    code = models.CharField(max_length=50, unique=True, editable=False, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.code = f"{self.MODEL_CODE}-{self.pk}"
            super().save(update_fields=["code"])


class TimeStampedModel(models.Model):
    """Adds created_at and updated_at timestamp fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class AuditableModel(models.Model):
    """Adds created_at, created_by, updated_at, updated_by fields."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
    )
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class CreatedAtModel(models.Model):
    """Adds created_at field."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class ActivatableModel(models.Model):
    """Adds is_active=TRUE/FALSE field."""

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class NamedModel(models.Model):
    """Adds name field with MAX_LENGTH=255."""

    name = models.CharField(max_length=255, db_index=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class DescriptionModel(models.Model):
    """Adds description field."""

    description = models.CharField(blank=True)

    class Meta:
        abstract = True
