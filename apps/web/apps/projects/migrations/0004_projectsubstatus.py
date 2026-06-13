import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0003_projectstatus"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectSubStatus",
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
                (
                    "code",
                    models.CharField(
                        db_index=True, editable=False, max_length=50, unique=True
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
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
                    "main_status",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_statuses",
                        to="projects.projectstatus",
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
            ],
            options={
                "ordering": ["main_status", "order", "name"],
                "permissions": [
                    ("import_projectsubstatus", "Can import project sub-statuses"),
                    ("export_projectsubstatus", "Can export project sub-statuses"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("name", "main_status"),
                        name="projects_projectsubstatus_name_main_status_uniq",
                    ),
                    models.UniqueConstraint(
                        fields=("main_status", "order"),
                        name="projects_projectsubstatus_main_status_order_uniq",
                    ),
                ],
            },
        ),
    ]
