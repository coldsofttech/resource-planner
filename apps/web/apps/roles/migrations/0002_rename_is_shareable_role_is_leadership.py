from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("roles", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="role",
            old_name="is_shareable",
            new_name="is_leadership",
        ),
    ]
