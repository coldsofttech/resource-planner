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


_FINANCIAL_YEAR_DEFAULTS = {
    "FY_EXPIRY_WARNING_DAYS": {
        "label": "FY Expiry Warning Days",
        "value": "30",
        "description": (
            "Number of days before the active financial year's end date at which a "
            "warning banner is shown at the top of every page."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "financial_year",
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


_SPRINT_DEFAULTS = {
    "SPRINT_NAME_PREFIX": {
        "label": "Sprint Name Prefix",
        "value": "Sprint",
        "description": (
            "Prefix used when auto-generating sprint names. "
            "For example, 'Sprint', 'SP', etc."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "sprints",
    },
    "SPRINT_START_NUMBER": {
        "label": "Sprint Start Number",
        "value": "1",
        "description": (
            "The starting number used when generating the first sprint of "
            "a financial year if no existing sprints are found."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "sprints",
    },
    "SPRINT_DURATION_DAYS": {
        "label": "Sprint Duration (days)",
        "value": "14",
        "description": (
            "Number of calendar days in a sprint. Typically set to 14 days (2 weeks)."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "sprints",
    },
    "SPRINT_POINT_PRICE": {
        "label": "Sprint Point Price (£)",
        "value": "1150",
        "description": (
            "Day rate in GBP (£) used for calculating sprint cost "
            "based on story points. "
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "sprints",
    },
}


_USERS_DEFAULTS = {
    "PASSWORD_RESET_TIMEOUT": {
        "label": "Admin Password Reset Timeout (minutes)",
        "value": "120",
        "description": (
            "Number of minutes before an admin-initiated password reset link expires. "
            "Default is 120 minutes (2 hours)."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "users",
    },
}


_PROJECT_DEFAULTS = {
    "PROJECT_SIZE_XS_MAX_AMOUNT": {
        "label": "Project Size XS — Max Amount (£)",
        "value": "20000",
        "description": (
            "Maximum budget amount (£) for an XS (extra-small) project. "
            "Projects with a total budget at or below this value are classified as XS."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "projects",
    },
    "PROJECT_SIZE_S_MAX_AMOUNT": {
        "label": "Project Size S — Max Amount (£)",
        "value": "60000",
        "description": (
            "Maximum budget amount (£) for an S (small) project. "
            "Projects with a total budget above XS and at or below this value are "
            "classified as S."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "projects",
    },
    "PROJECT_SIZE_M_MAX_AMOUNT": {
        "label": "Project Size M — Max Amount (£)",
        "value": "200000",
        "description": (
            "Maximum budget amount (£) for an M (medium) project. "
            "Projects with a total budget above S and at or below this value are "
            "classified as M."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "projects",
    },
    "PROJECT_SIZE_L_MAX_AMOUNT": {
        "label": "Project Size L — Max Amount (£)",
        "value": "500000",
        "description": (
            "Maximum budget amount (£) for an L (large) project. "
            "Projects with a total budget above M and at or below this value are "
            "classified as L. "
            "Projects exceeding this value are classified as XL."
        ),
        "data_type": "integer",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "projects",
    },
}


_AI_DEFAULTS = {
    "AI_ENABLED": {
        "label": "AI Enabled",
        "value": "false",
        "description": (
            "Master switch for AI-powered features. "
            "Set to 'true' to enable. When false, all features fall back to "
            "their deterministic implementations. Accepted values: true, false."
        ),
        "data_type": "boolean",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "ai",
    },
    "AI_PROVIDER": {
        "label": "AI Provider",
        "value": "anthropic",
        "description": (
            "AI provider to use. "
            "Accepted values: 'anthropic' (Anthropic API), 'bedrock' (AWS Bedrock). "
            "When set to 'bedrock', the AI_BEDROCK_* configs are also required."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "ai",
    },
    "AI_MODEL": {
        "label": "AI Model",
        "value": "",
        "description": (
            "Model identifier string. "
            "Anthropic example: claude-sonnet-4-20250514. "
            "Bedrock example: anthropic.claude-3-5-sonnet-20241022-v2:0 "
            "(full Bedrock model ID including version suffix)."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "ai",
    },
    "AI_ANTHROPIC_API_KEY": {
        "label": "Anthropic API Key",
        "value": "",
        "description": (
            "Anthropic API key (sk-ant-...). "
            "Required only when AI_PROVIDER=anthropic. "
            "Stored encrypted at rest."
        ),
        "data_type": "string",
        "is_secret": True,
        "is_admin": False,
        "module": "ai",
    },
    "AI_BEDROCK_REGION": {
        "label": "Bedrock Region",
        "value": "us-east-1",
        "description": (
            "AWS region for Bedrock API calls. "
            "Required when AI_PROVIDER=bedrock. "
            "Must be a region where the chosen model is available. "
            "Examples: us-east-1, eu-west-2, ap-southeast-1."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "ai",
    },
    "AI_BEDROCK_AUTH_MODE": {
        "label": "Bedrock Auth Mode",
        "value": "role",
        "description": (
            "Authentication mode for AWS Bedrock. "
            "'role' — no credentials stored; boto3 resolves via instance profile, "
            "ECS task role, or AWS_* environment variables. "
            "'user' — explicit IAM user credentials stored in AI_BEDROCK_IAM_KEY "
            "and AI_BEDROCK_IAM_SECRET. Use 'user' for local or on-premise deployments."
        ),
        "data_type": "string",
        "is_secret": False,  # nosec B105
        "is_admin": False,
        "module": "ai",
    },
    "AI_BEDROCK_IAM_KEY": {
        "label": "Bedrock IAM Access Key ID",
        "value": "",
        "description": (
            "AWS IAM user access key ID. "
            "Required only when AI_PROVIDER=bedrock and AI_BEDROCK_AUTH_MODE=user. "
            "The IAM user must have bedrock:InvokeModel permission on the chosen "
            "model. Stored encrypted at rest."
        ),
        "data_type": "string",
        "is_secret": True,
        "is_admin": False,
        "module": "ai",
    },
    "AI_BEDROCK_IAM_SECRET": {
        "label": "Bedrock IAM Secret Access Key",
        "value": "",
        "description": (
            "AWS IAM user secret access key. "
            "Required only when AI_PROVIDER=bedrock and AI_BEDROCK_AUTH_MODE=user. "
            "Stored encrypted at rest."
        ),
        "data_type": "string",
        "is_secret": True,
        "is_admin": False,
        "module": "ai",
    },
}


CONFIGURATION_DEFAULTS = {
    **_SETUP_DEFAULTS,
    **_GENERAL_DEFAULTS,
    **_AUTH_DEFAULTS,
    **_INFRA_DEFAULTS,
    **_EMAIL_DEFAULTS,
    **_FINANCIAL_YEAR_DEFAULTS,
    **_HOLIDAYS_DEFAULTS,
    **_SPRINT_DEFAULTS,
    **_USERS_DEFAULTS,
    **_PROJECT_DEFAULTS,
    **_AI_DEFAULTS,
}
