from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    BaseModel,
    CodeModel,
    IconModel,
)


class OAuth(BaseModel, AuditableModel, ActivatableModel, CodeModel, IconModel):
    MODEL_CODE = "OAUTH"

    name = models.CharField(max_length=100, db_index=True, unique=True)
    client_id = models.CharField(max_length=500)
    client_secret = models.CharField(max_length=500)
    auth_endpoint = models.URLField()
    token_endpoint = models.URLField()
    userinfo_endpoint = models.URLField()
    scope = models.CharField(max_length=500)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name
