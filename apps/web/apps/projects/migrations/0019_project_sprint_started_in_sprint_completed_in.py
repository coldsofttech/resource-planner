import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0018_projectcomment"),
        ("sprints", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="sprint_started_in",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects_started_in",
                to="sprints.sprint",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="sprint_completed_in",
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects_completed_in",
                to="sprints.sprint",
            ),
        ),
    ]
