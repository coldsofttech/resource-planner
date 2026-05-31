from apps.saml.models import SAML


def provider_exists(name: str):
    return SAML.objects.filter(name=name).exists()


def get_active_provider_by_code(code: str):
    try:
        return SAML.objects.get(code=code, is_active=True)
    except SAML.DoesNotExist:
        return None


def get_provider_by_entity_id(entity_id: str):
    return SAML.objects.filter(idp_entity_id=entity_id, is_active=True).first()
