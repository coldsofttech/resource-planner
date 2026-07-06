from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0026_onboarding_business_unit_m2m"),
    ]

    operations = [
        migrations.RenameField(
            model_name="onboardingattachment",
            old_name="name",
            new_name="file_name",
        ),
        migrations.AlterModelOptions(
            name="onboardingattachment",
            options={"ordering": ["file_name"]},
        ),
        migrations.AddField(
            model_name="onboardingattachment",
            name="content_type",
            field=models.CharField(default="", max_length=255),
        ),
        migrations.AddField(
            model_name="onboardingattachment",
            name="file_size",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="onboardingattachment",
            name="file_path",
            field=models.TextField(default=""),
        ),
    ]
