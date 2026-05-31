from apps.users.models import GROUP_ADMINISTRATORS, GROUP_GUESTS, User


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


def get_system_group(name: str):
    from django.contrib.auth.models import Group

    try:
        return Group.objects.get(name=name)
    except Group.DoesNotExist:
        return None


def get_administrators_group():
    return get_system_group(GROUP_ADMINISTRATORS)


def get_guests_group():
    return get_system_group(GROUP_GUESTS)
