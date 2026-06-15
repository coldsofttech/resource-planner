from django.db.models import Count, QuerySet

from apps.users.models import (
    GROUP_ADMINISTRATORS,
    GROUP_GUESTS,
    Group,
    GroupProfile,
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


def get_all_users() -> QuerySet[UserProfile]:
    return UserProfile.objects.select_related(
        "user",
        "sso_provider_content_type",
        "created_by",
        "updated_by",
    ).order_by("user__last_name", "user__first_name")


def get_user_by_profile_code(code: str) -> UserProfile | None:
    try:
        return UserProfile.objects.select_related(
            "user",
            "sso_provider_content_type",
            "created_by",
            "updated_by",
        ).get(code=code)
    except UserProfile.DoesNotExist:
        return None


def get_all_groups() -> QuerySet[GroupProfile]:
    return (
        GroupProfile.objects.select_related("group", "created_by", "updated_by")
        .annotate(member_count=Count("group__user"))
        .order_by("group__name")
    )


def get_group_by_code(code: str) -> GroupProfile | None:
    try:
        return (
            GroupProfile.objects.select_related("group", "created_by", "updated_by")
            .annotate(member_count=Count("group__user"))
            .get(code=code)
        )
    except GroupProfile.DoesNotExist:
        return None


def get_group_members(code: str) -> QuerySet[UserProfile]:
    return (
        UserProfile.objects.filter(user__groups__profile__code=code)
        .select_related("user", "created_by", "updated_by")
        .prefetch_related("user__avatars")
        .order_by("user__last_name", "user__first_name")
    )
