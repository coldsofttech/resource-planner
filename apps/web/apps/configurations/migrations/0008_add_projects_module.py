from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("configurations", "0007_alter_configuration_module"),
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
                    ("sprints", "Sprints"),
                    ("users", "Users"),
                    ("projects", "Projects"),
                ],
                default="general",
                max_length=30,
            ),
        ),
    ]
