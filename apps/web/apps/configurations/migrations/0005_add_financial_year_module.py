from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("configurations", "0004_add_holidays_module"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuration",
            name="module",
            field=models.CharField(
                choices=[
                    ("setup", "Setup"),
                    ("general", "General"),
                    ("auth", "Authentication"),
                    ("infra", "Infrastructure"),
                    ("email", "Email"),
                    ("holidays", "Holidays"),
                    ("financial_year", "Financial Year"),
                ],
                default="general",
                max_length=30,
            ),
        ),
    ]
