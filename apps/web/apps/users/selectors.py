from apps.users.models import User


def user_exists(email: str):
    return User.objects.filter(email=email).exists()


def superuser_exists():
    return User.objects.filter(is_superuser=True).exists()


def is_superuser(email: str):
    return User.objects.filter(email=email, is_superuser=True).exists()


def get_user(email: str):
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None
