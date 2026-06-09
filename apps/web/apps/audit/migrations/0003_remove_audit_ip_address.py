from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "audit",
            "0002_rename_audit_audit_module_resource_type_idx_audit_audit_module_7ca1b2_idx_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="audit",
            name="ip_address",
        ),
    ]
