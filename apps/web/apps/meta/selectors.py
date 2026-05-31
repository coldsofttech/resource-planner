def get_public_meta():
    from apps.configurations.selectors import Auth, General, Setup

    return {
        "setup_complete": Setup.get_setup_complete(),
        "app_name": General.get_app_name(),
        "auth_mode": Auth.get_auth_mode().value,
        "allow_registration": Auth.get_allow_registration(),
    }


def get_user_meta(user):
    full_name = f"{user.first_name} {user.last_name}".strip()

    return {
        "name": full_name or user.username,
        "email": user.email,
        "is_superuser": user.is_superuser,
    }
