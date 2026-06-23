import decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0019_project_sprint_started_in_sprint_completed_in"),
        ("recharges", "0002_alter_projecttypemapping_options"),
        ("sprints", "0020_sprintdataimportconfirmed"),
        ("teams", "0005_alter_assignment_created_by_and_more"),
        ("users", "0011_add_groupprofile_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RechargeDetail",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("code", models.CharField(blank=True, db_index=True, max_length=50)),
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
                    "assignee",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recharge_details",
                        to="users.userprofile",
                    ),
                ),
                (
                    "import_record",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharge_details",
                        to="sprints.sprintdataimport",
                    ),
                ),
                (
                    "label",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recharge_details",
                        to="projects.projectlabel",
                    ),
                ),
                (
                    "programme",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recharge_details",
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
                        related_name="recharge_details",
                        to="projects.project",
                    ),
                ),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharge_details",
                        to="sprints.sprint",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharge_details",
                        to="teams.team",
                    ),
                ),
            ],
            options={
                "ordering": ["sprint", "team", "assignee"],
            },
        ),
    ]
