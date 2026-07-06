import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recharges", "0010_alter_rechargeprojectgroup_code_and_more"),
        ("sprints", "0022_alter_sprintdataimport_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RechargeEmail",
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
                ("to", models.JSONField(default=list)),
                ("cc", models.JSONField(default=list)),
                ("subject", models.CharField(blank=True, default="", max_length=500)),
                ("body", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("error", "Error"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, default="")),
                ("sent_data", models.JSONField(default=dict)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_%(class)s_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_%(class)s_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharge_emails",
                        to="recharges.rechargeprojectgroup",
                    ),
                ),
                (
                    "sprint",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recharge_emails",
                        to="sprints.sprint",
                    ),
                ),
            ],
            options={
                "ordering": ["sprint", "type", "group"],
            },
        ),
        migrations.AddConstraint(
            model_name="rechargeemail",
            constraint=models.UniqueConstraint(
                fields=["sprint", "type", "group"],
                name="recharges_rechargeemail_sprint_type_group_uniq",
            ),
        ),
    ]
