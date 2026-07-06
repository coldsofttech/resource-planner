import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recharges", "0006_rechargedetail_jira_id_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="rechargedetail",
            name="recharge_type",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recharge_details",
                to="recharges.rechargetype",
            ),
        ),
        migrations.AddField(
            model_name="recharge",
            name="recharge_type",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="recharges",
                to="recharges.rechargetype",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="recharge",
            name="recharges_recharge_sprint_type_programme_project_uniq",
        ),
        migrations.AddConstraint(
            model_name="recharge",
            constraint=models.UniqueConstraint(
                fields=["sprint", "type", "programme", "project", "recharge_type"],
                name="recharges_recharge_sprint_type_programme_project_recha_a25ae731",
            ),
        ),
    ]
