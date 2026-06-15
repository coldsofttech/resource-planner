from django.db import migrations, models


def set_default_sort_orders(apps, schema_editor):
    ProjectStatus = apps.get_model("projects", "ProjectStatus")
    order_map = {
        "New": 10,
        "In Progress": 20,
        "On Hold": 30,
        "Completed": 40,
        "Cancelled": 50,
    }
    for name, order in order_map.items():
        ProjectStatus.objects.filter(name=name).update(sort_order=order)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0013_rename_efforts_issues_to_efforts_issued"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectstatus",
            name="sort_order",
            field=models.PositiveIntegerField(default=0, db_index=True),
        ),
        migrations.AlterModelOptions(
            name="projectstatus",
            options={
                "ordering": ["sort_order", "name"],
                "permissions": [
                    ("export_projectstatus", "Can export project statuses")
                ],
            },
        ),
        migrations.RunPython(set_default_sort_orders, migrations.RunPython.noop),
    ]
