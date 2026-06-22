import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0008_add_fk_fields_to_sprintdataimportrow"),
    ]

    operations = [
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="sprint_code",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="import_rows",
                to="sprints.sprint",
            ),
        ),
    ]
