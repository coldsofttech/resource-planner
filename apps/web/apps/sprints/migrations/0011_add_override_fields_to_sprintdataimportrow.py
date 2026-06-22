import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0019_project_sprint_started_in_sprint_completed_in"),
        ("recharges", "0002_alter_projecttypemapping_options"),
        ("sprints", "0010_sprintdataimportrow_is_manually_added"),
        ("users", "0011_add_groupprofile_permissions"),
    ]

    operations = [
        # Text override fields (NULL = no override set)
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="story_type_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="jira_id_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="title_override",
            field=models.CharField(blank=True, default=None, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="assignee_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="efforts_override",
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="sprint_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="label_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="mapping_override",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        # FK override fields
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="assignee_code_override",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sprint_import_rows_as_assignee_override",
                to="users.userprofile",
            ),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="label_code_override",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sprint_import_rows_label_override",
                to="projects.projectlabel",
            ),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="mapping_code_override",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sprint_import_rows_mapping_override",
                to="recharges.rechargetype",
            ),
        ),
        migrations.AddField(
            model_name="sprintdataimportrow",
            name="sprint_code_override",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="import_rows_override",
                to="sprints.sprint",
            ),
        ),
    ]
