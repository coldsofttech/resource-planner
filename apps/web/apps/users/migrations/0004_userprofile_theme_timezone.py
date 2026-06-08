from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_groupprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="theme",
            field=models.CharField(
                choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
                default="light",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="timezone",
            field=models.CharField(blank=True, default="UTC", max_length=100),
        ),
    ]
