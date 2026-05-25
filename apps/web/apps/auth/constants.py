from django.db import models


class AuthMode(models.TextChoices):
    CLASSIC = "classic", "Classic"
    SAML = "saml", "SAML"
    OAUTH = "oauth", "OAuth"
