from django.db import models


class DataType(models.TextChoices):
    STRING = "string", "String"
    INTEGER = "integer", "Integer"
    FLOAT = "float", "Float"
    BOOLEAN = "boolean", "Boolean"


class Module(models.TextChoices):
    SETUP = "setup", "Setup"
    GENERAL = "general", "General"
    AUTHENTICATION = "auth", "Authentication"
    INFRA = "infra", "Infrastructure"
    EMAIL = "email", "Email"
    HOLIDAYS = "holidays", "Holidays"
    FINANCIAL_YEAR = "financial_year", "Financial Year"
    SPRINTS = "sprints", "Sprints"
    USERS = "users", "Users"
    PROJECTS = "projects", "Projects"
    AI = "ai", "AI"
    SECURITY = "security", "Security"
    SECURITY_PASSWORD = "security_password", "Security - Password"
    WINS = "wins", "Wins"
