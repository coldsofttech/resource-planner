from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0009_add_sprint_code_to_sprintdataimportrow"),
    ]

    operations = [
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="is_manually_added",
            field=models.BooleanField(default=False),
        ),
    ]
