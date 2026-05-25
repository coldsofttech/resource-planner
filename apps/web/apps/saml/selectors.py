from apps.saml.models import SAML


def provider_exists(name: str):
    return SAML.objects.filter(name=name).exists()
