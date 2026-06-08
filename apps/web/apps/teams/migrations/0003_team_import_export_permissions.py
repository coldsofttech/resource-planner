from django.db import migrations


class Migration(migrations.Migration):
    """Add import_team and export_team custom permissions to Team."""

    dependencies = [
        ("teams", "0002_alter_team_created_by_alter_team_updated_by"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="team",
            options={
                "ordering": ["name"],
                "permissions": [
                    ("import_team", "Can import teams"),
                    ("export_team", "Can export teams"),
                ],
            },
        ),
    ]
