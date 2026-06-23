from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sprints", "0020_sprintdataimportconfirmed"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sprintdataimport",
            options={
                "permissions": [
                    ("import_forecast", "Can upload forecast data for a sprint team"),
                    ("import_actuals", "Can upload actuals data for a sprint team"),
                    ("review_forecast", "Can run review checks on a forecast import"),
                    ("confirm_forecast", "Can confirm a reviewed forecast import"),
                    ("review_complete", "Can mark sprint forecast review complete"),
                ]
            },
        ),
    ]
