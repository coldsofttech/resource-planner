from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("business_units", "0001_initial"),
        ("projects", "0025_onboarding"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="onboarding",
            name="business_unit",
        ),
        migrations.AddField(
            model_name="onboarding",
            name="business_units",
            field=models.ManyToManyField(
                blank=True,
                related_name="onboardings",
                to="business_units.businessunit",
            ),
        ),
    ]
