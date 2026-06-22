from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0017_sprint_data_import_review_complete"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sprintdataimport",
            options={
                "ordering": ["-version_number"],
                "permissions": [
                    ("import_forecast", "Can upload forecast data for a sprint team"),
                    ("import_actuals", "Can upload actuals data for a sprint team"),
                    ("review_forecast", "Can run review checks on a forecast import"),
                    ("confirm_forecast", "Can confirm a reviewed forecast import"),
                ],
            },
        ),
    ]
