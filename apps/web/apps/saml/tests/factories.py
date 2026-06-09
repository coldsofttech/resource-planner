from apps.saml.models import SAML

PROVIDER_BASE = {
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


def make_provider(name: str = "Test Provider", **overrides) -> SAML:
    return SAML.objects.create(name=name, **{**PROVIDER_BASE, **overrides})
