from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0011_add_override_fields_to_sprintdataimportrow"),
    ]

    operations = [
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="is_deleted",
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
