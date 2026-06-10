import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0003_team_import_export_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Assignment",
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
                    "updated_at",
                    models.DateTimeField(auto_now=True, db_index=True),
                ),
                (
                    "note",
                    models.TextField(blank=True, default=""),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_assignment_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="team_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="teams.team",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="updated_assignment_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "permissions": [
                    ("assign_team", "Can assign members to teams"),
                    ("unassign_team", "Can unassign members from teams"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="assignment",
            constraint=models.UniqueConstraint(
                fields=["member", "team"],
                name="teams_assignment_member_team_uniq",
            ),
        ),
        migrations.CreateModel(
            name="AssignmentHistory",
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
                    "moved_on",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("ASSIGN", "Assign"),
                            ("UNASSIGN", "Unassign"),
                            ("MOVE", "Move"),
                        ],
                        db_index=True,
                        max_length=10,
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="team_assignment_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "from_team",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assignment_history_from",
                        to="teams.team",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="team_assignment_history",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "to_team",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assignment_history_to",
                        to="teams.team",
                    ),
                ),
            ],
            options={
                "ordering": ["-moved_on"],
            },
        ),
    ]
