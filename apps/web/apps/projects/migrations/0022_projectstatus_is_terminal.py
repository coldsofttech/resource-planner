from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0021_projectactuals"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectstatus",
            name="is_terminal",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
