from django.db import migrations


class Migration(migrations.Migration):
    """Add export_member custom permission to UserProfile."""

    dependencies = [
        ("users", "0008_add_workforce_fields_to_userprofile"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="userprofile",
            options={
                "ordering": ["user"],
                "permissions": [
                    ("change_user_workforce", "Can change user workforce details"),
                    ("export_member", "Can export members"),
                ],
            },
        ),
    ]
