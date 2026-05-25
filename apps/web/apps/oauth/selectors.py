from apps.oauth.models import OAuth


def provider_exists(name: str):
    return OAuth.objects.filter(name=name).exists()
