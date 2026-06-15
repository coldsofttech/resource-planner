from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_add_export_member_permission"),
    ]

    operations = [
        migrations.AddField(
            model_name="groupprofile",
            name="is_active",
            field=models.BooleanField(default=True, db_index=True),
        ),
    ]
