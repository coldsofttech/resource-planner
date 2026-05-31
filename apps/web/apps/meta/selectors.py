def _sso_provider_dict(provider) -> dict:
    return {"code": provider.code, "name": provider.name, "icon": provider.icon}


def get_public_meta():
    from apps.auth.constants import AuthMode
    from apps.configurations.selectors import Auth, General, Setup

    auth_mode = Auth.get_auth_mode()
    data: dict = {
        "setup_complete": Setup.get_setup_complete(),
        "app_name": General.get_app_name(),
        "auth_mode": auth_mode.value,
        "allow_registration": Auth.get_allow_registration(),
        "oauth_provider": None,
        "saml_provider": None,
    }

    if auth_mode == AuthMode.OAUTH:
        from apps.oauth.selectors import get_active_provider as get_active_oauth

        provider = get_active_oauth()
        if provider:
            data["oauth_provider"] = _sso_provider_dict(provider)

    elif auth_mode == AuthMode.SAML:
        from apps.saml.selectors import get_active_provider as get_active_saml

        provider = get_active_saml()
        if provider:
            data["saml_provider"] = _sso_provider_dict(provider)

    return data


def get_user_meta(user):
    full_name = f"{user.first_name} {user.last_name}".strip()

    return {
        "name": full_name or user.username,
        "email": user.email,
        "is_superuser": user.is_superuser,
    }
