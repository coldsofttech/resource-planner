from django.db import models

from apps.core.models import ActivatableModel, AuditableModel, BaseModel, CodeModel


class SAML(BaseModel, AuditableModel, ActivatableModel, CodeModel):
    MODEL_CODE = "SAML"

    name = models.CharField(max_length=100, db_index=True, unique=True)
    idp_entity_id = models.URLField()
    idp_sso_url = models.URLField()
    idp_x509_cert = models.CharField()
    sp_entity_id = models.URLField(blank=True)
    sp_assertion_url = models.URLField()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name
