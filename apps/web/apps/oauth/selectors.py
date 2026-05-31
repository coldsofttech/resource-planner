from apps.oauth.models import OAuth


def provider_exists(name: str):
    return OAuth.objects.filter(name=name).exists()


def get_active_provider_by_code(code: str):
    try:
        return OAuth.objects.get(code=code, is_active=True)
    except OAuth.DoesNotExist:
        return None
