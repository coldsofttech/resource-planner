import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "recharges",
            "0008_remove_recharge_recharges_recharge_sprint_type_programme_project_recha_a25ae731_and_more",
        ),
        ("projects", "0024_projectactualconfig"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RechargeProjectGroup",
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
                        blank=True, db_index=True, max_length=50, unique=True
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "projects",
                    models.ManyToManyField(
                        blank=True,
                        related_name="recharge_project_groups",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="rechargeprojectgroup",
            constraint=models.UniqueConstraint(
                fields=["name"],
                name="recharges_rechargeprojectgroup_name_uniq",
            ),
        ),
    ]
