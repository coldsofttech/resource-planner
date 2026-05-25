from apps.users.models import User


def user_exists(email: str):
    return User.objects.filter(email=email).exists()


def superuser_exists():
    return User.objects.filter(is_superuser=True).exists()
