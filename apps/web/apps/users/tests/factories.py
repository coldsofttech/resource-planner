from apps.users.models import Group, GroupProfile, User, UserProfile


def make_user(
    email: str = "user@example.com",
    password: str = "StrongPass123!",
    is_active: bool = True,
    is_superuser: bool = False,
    **kwargs,
) -> User:
    if is_superuser:
        return User.objects.create_superuser(
            username=email, email=email, password=password, **kwargs
        )
    return User.objects.create_user(
        username=email,
        email=email,
        password=password,
        is_active=is_active,
        **kwargs,
    )  # nosec B106


def make_superuser(
    email: str = "admin@example.com",
    password: str = "StrongPass123!",
    **kwargs,
) -> User:
    return make_user(email=email, password=password, is_superuser=True, **kwargs)


def make_group(name: str = "Test Group") -> Group:
    return Group.objects.create(name=name)


def make_profile(user: User | None = None, **kwargs) -> UserProfile:
    if user is None:
        user = make_user()
    return UserProfile.objects.create(user=user, **kwargs)


def make_user_with_profile(email: str = "user@example.com") -> tuple[User, UserProfile]:
    user = make_user(email)
    profile = UserProfile.objects.create(user=user)
    return user, profile


def make_group_with_profile(
    name: str = "Test Group",
) -> tuple[Group, GroupProfile]:
    group = make_group(name)
    profile = GroupProfile.objects.create(group=group)
    return group, profile
