from django.db.models import QuerySet

from apps.users.models import (
    GROUP_ADMINISTRATORS,
    GROUP_GUESTS,
    Group,
    User,
    UserProfile,
)


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
    try:
        return Group.objects.get(name=name)
    except Group.DoesNotExist:
        return None


def get_administrators_group():
    return get_system_group(GROUP_ADMINISTRATORS)


def get_guests_group():
    return get_system_group(GROUP_GUESTS)


def get_all_members() -> QuerySet[UserProfile]:
    return (
        UserProfile.objects.select_related(
            "user",
            "location",
            "employment_type",
            "role",
            "created_by",
            "updated_by",
        )
        .prefetch_related("skills", "user__avatars", "user__team_assignments__team")
        .order_by("user__last_name", "user__first_name")
    )


def get_member_by_code(code: str) -> UserProfile | None:
    try:
        return (
            UserProfile.objects.select_related(
                "user",
                "location",
                "employment_type",
                "role",
                "created_by",
                "updated_by",
            )
            .prefetch_related("user__avatars", "user__team_assignments__team")
            .get(code=code)
        )
    except UserProfile.DoesNotExist:
        return None
