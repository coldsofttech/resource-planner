import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0004_projectsubstatus"),
        ("teams", "0005_alter_assignment_created_by_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
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
                ("name", models.CharField(db_index=True, max_length=255)),
                ("description", models.CharField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_index=True),
                ),
                (
                    "display_name",
                    models.CharField(blank=True, db_index=True, max_length=255),
                ),
                (
                    "efforts_issues",
                    models.BooleanField(db_index=True, default=False),
                ),
                ("commitment_date", models.DateField(blank=True, null=True)),
                (
                    "run_cost_applies",
                    models.BooleanField(db_index=True, default=False),
                ),
                (
                    "confidence",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("very_high", "Very High"),
                        ],
                        db_index=True,
                        max_length=20,
                        null=True,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("very_high", "Very High"),
                        ],
                        db_index=True,
                        max_length=20,
                        null=True,
                    ),
                ),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "assigned_team",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_projects",
                        to="teams.team",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_project_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "programme",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="projects",
                        to="projects.programme",
                    ),
                ),
                (
                    "project_type",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="projects",
                        to="projects.projecttype",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="projects",
                        to="projects.projectstatus",
                    ),
                ),
                (
                    "sub_status",
                    models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="projects",
                        to="projects.projectsubstatus",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_project_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "permissions": [
                    ("import_project", "Can import projects"),
                    ("export_project", "Can export projects"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ProjectCollaborator",
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
                    "created_at",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "added_on",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "project",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="collaborators",
                        to="projects.project",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="collaborating_projects",
                        to="teams.team",
                    ),
                ),
            ],
            options={
                "ordering": ["added_on"],
            },
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                fields=["name"], name="projects_project_name_uniq"
            ),
        ),
        migrations.AddConstraint(
            model_name="projectcollaborator",
            constraint=models.UniqueConstraint(
                fields=["project", "team"],
                name="projects_projectcollaborator_project_team_uniq",
            ),
        ),
    ]
