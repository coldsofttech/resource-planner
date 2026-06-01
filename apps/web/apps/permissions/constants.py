from django.db import models


class PermissionScope(models.IntegerChoices):
    NONE = 0, "None"
    SELF = 1, "Self"  # records owned by / created by the user
    TEAM = 2, "Team"  # records within the user's team(s)
    ALL = 3, "All"  # unrestricted
