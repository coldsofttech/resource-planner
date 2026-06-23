from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recharges", "0005_recharge"),
    ]

    operations = [
        migrations.AddField(
            model_name="rechargedetail",
            name="jira_id",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="rechargedetail",
            name="title",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
