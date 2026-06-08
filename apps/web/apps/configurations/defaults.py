_SETUP_DEFAULTS = {
    "SETUP_COMPLETE": {
        "label": "Initial Setup Complete",
        "value": "false",
        "description": "Marks whether the initial setup wizard has been completed.",
        "data_type": "boolean",
        "is_secret": False,  # nosec B105
        "is_admin": True,
        "module": "setup",
    },
}

_GENERAL_DEFAULTS = {
    "APP_NAME": {
        "label": "Application Name",
        "value": "Resource<b>Planner</b>",
        "description": (
            "Display name shown in the navigation bar and browser tab title. "
            "HTML tags are supported for custom styling (e.g. bold, colour, icon)."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "general",
    },
    "APP_URL": {
        "label": "Application URL",
        "value": "",
        "description": (
            "Absolute base URL of this deployment (e.g. https://resourceplanner.com). "
            "Used to generate SSO redirect URIs and email links. No trailing slash."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "general",
    },
}

_AUTH_DEFAULTS = {
    "AUTH_MODE": {
        "label": "Authentication Mode",
        "value": "classic",
        "description": (
            "Controls how users authenticate. Supported are: classic, saml, oauth."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "auth",
    },
    "ALLOW_REGISTRATION": {
        "label": "Allow Self-Registration",
        "value": "true",
        "description": (
            "When AUTH_MODE=classic, allow new users to create their own account via "
            "the /register/ page. Set to 'false' to restrict access to admin-created "
            "accounts only."
        ),
        "data_type": "boolean",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "auth",
    },
}

_INFRA_DEFAULTS = {
    "DEPLOYMENT_TYPE": {
        "label": "Deployment Type",
        "value": "local",
        "description": (
            "Deployment mode. 'local' stores secrets with Fernet encryption in the "
            "database. 'aws' stores secrets in AWS Secrets Manager."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": True,
        "module": "infra",
    },
    "SECRETS_PREFIX": {
        "label": "Secrets Prefix",
        "value": "",
        "description": (
            "AWS Secrets Manager prefix (e.g. /resourceplanner). Empty means secrets "
            "are stored locally in the database using Fernet encryption."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "infra",
    },
    "STORAGE_TYPE": {
        "label": "Storage Type",
        "value": "database",
        "description": (
            "Storage mode. 'database' stores files within database. 'filesystem' "
            "stores files within local/server folder. 's3' stores files within "
            "Amazon S3 bucket."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": True,
        "module": "infra",
    },
    "STORAGE_PATH": {
        "label": "Storage Path",
        "value": "",
        "description": (
            "Storage path. In case of 'filesystem' path of local/server folder. "
            "In case of 's3', S3 bucket arn."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": True,
        "module": "infra",
    },
}

_EMAIL_DEFAULTS = {
    "EMAIL_TYPE": {
        "label": "Email Type",
        "value": "console",
        "description": (
            "Email type. 'console' triggers email within the terminal (for local "
            "developments). 'smtp' to trigger actual email with encryption support."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_FROM_ADDRESS": {
        "label": "From Email Address",
        "value": "noreply@resourceplanner.local",
        "description": (
            "The 'From' address used for all outbound emails (password resets, "
            "notifications, etc.)."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_FROM_NAME": {
        "label": "From Name",
        "value": "Resource Planner",
        "description": (
            "The name for the 'From' address used for all outbound emails (password "
            "resets, notifications, etc.)."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_HOST": {
        "label": "SMTP Host",
        "value": "",
        "description": "Hostname or IP address of the outbound SMTP server.",
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_PORT": {
        "label": "SMTP Port",
        "value": "587",
        "description": (
            "TCP port for the SMTP server (25 = plain, 587 = STARTTLS, 465 = SSL/TLS)."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_ENC_TYPE": {
        "label": "SMTP Encryption Type",
        "value": "none",
        "description": (
            "Transport-layer security for SMTP. 'none' = plain, 'starttls' = STARTTLS, "
            "'ssl' = SSL/TLS."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_AUTH_ENABLED": {
        "label": "SMTP Authentication Enabled",
        "value": "false",
        "description": (
            "Whether the SMTP server requires username/password authentication."
        ),
        "data_type": "boolean",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_USERNAME": {
        "label": "SMTP Username",
        "value": "",
        "description": (
            "Username for SMTP authentication (only used when auth is enabled)."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "email",
    },
    "EMAIL_SMTP_PASSWORD": {
        "label": "SMTP Password",
        "value": "",
        "description": "Password for SMTP authentication. Stored encrypted.",
        "data_type": "string",
        "is_secret": True,
        "is_admin": False,
        "module": "email",
    },
}


_HOLIDAYS_DEFAULTS = {
    "DEFAULT_HOLIDAYS": {
        "label": "Default Holidays",
        "value": "20",
        "description": (
            "Number of holiday days allocated to each team member per financial year. "
            "Used as the baseline when calculating available capacity in sprint "
            "planning."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "holidays",
    },
}


CONFIGURATION_DEFAULTS = {
    **_SETUP_DEFAULTS,
    **_GENERAL_DEFAULTS,
    **_AUTH_DEFAULTS,
    **_INFRA_DEFAULTS,
    **_EMAIL_DEFAULTS,
    **_HOLIDAYS_DEFAULTS,
}
