import decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0019_project_sprint_started_in_sprint_completed_in"),
        ("recharges", "0004_alter_rechargedetail_code_and_more"),
        ("sprints", "0020_sprintdataimportconfirmed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Recharge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "code",
                    models.CharField(
                        db_index=True, editable=False, max_length=50, unique=True
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("forecast", "Forecast"), ("actual", "Actual")],
                        db_index=True,
                        default="forecast",
                        max_length=20,
                    ),
                ),
                (
                    "total_days",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0"),
                        max_digits=10,
                    ),
                ),
                (
                    "total_cost",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0"),
                        max_digits=15,
                    ),
                ),
                (
                    "finance_contacts",
                    models.ManyToManyField(
                        blank=True,
                        limit_choices_to={"role": "finance"},
                        related_name="recharge_finance_set",
                        to="projects.projectcontact",
                    ),
                ),
                (
                    "programme",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recharges",
                        to="projects.programme",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recharges",
                        to="projects.project",
                    ),
                ),
                (
                    "project_contacts",
                    models.ManyToManyField(
                        blank=True,
                        limit_choices_to={"role": "project"},
                        related_name="recharge_project_set",
                        to="projects.projectcontact",
                    ),
                ),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharges",
                        to="sprints.sprint",
                    ),
                ),
            ],
            options={
                "ordering": ["sprint", "type", "programme", "project"],
            },
        ),
        migrations.AddConstraint(
            model_name="recharge",
            constraint=models.UniqueConstraint(
                fields=["sprint", "type", "programme", "project"],
                name="recharges_recharge_sprint_type_programme_project_uniq",
            ),
        ),
    ]
