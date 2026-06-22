from django.db import migrations, models


def backfill_codes(apps, schema_editor):
    SprintDataImport = apps.get_model("sprints", "SprintDataImport")
    for obj in SprintDataImport.objects.all():
        obj.code = f"SPTIMP-{obj.pk}"
        obj.save(update_fields=["code"])


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0005_sprint_data_import"),
    ]

    operations = [
        # Add code without unique constraint first so backfill works on existing rows
        migrations.AddField(
            model_name="sprintdataimport",
            name="code",
            field=models.CharField(
                blank=True, db_index=True, editable=False, max_length=50, default=""
            ),
        ),
        migrations.AddField(
            model_name="sprintdataimport",
            name="file_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(backfill_codes, migrations.RunPython.noop),
        # Now enforce uniqueness after all rows have a code
        migrations.AlterField(
            model_name="sprintdataimport",
            name="code",
            field=models.CharField(
                db_index=True, editable=False, max_length=50, unique=True
            ),
        ),
    ]
