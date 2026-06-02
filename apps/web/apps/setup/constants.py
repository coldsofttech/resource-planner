from django.db import models


class DeploymentType(models.TextChoices):
    LOCAL = "local", "Local"
    AWS = "aws", "AWS"


class DatabaseType(models.TextChoices):
    SQLITE = "sqlite", "SQLite"
    POSTGRESQL = "postgresql", "PostgreSQL"


class StorageType(models.TextChoices):
    DATABASE = "database", "Database"
    FILE_SYSTEM = "filesystem", "File System"
    AMAZON_S3 = "s3", "Amazon S3"


class EmailType(models.TextChoices):
    CONSOLE = "console", "Console"
    SMTP = "smtp", "SMTP"
