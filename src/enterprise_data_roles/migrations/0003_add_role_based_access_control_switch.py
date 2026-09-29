from django.db import migrations

from enterprise_data_roles.constants import ROLE_BASED_ACCESS_CONTROL_SWITCH


def create_switch(apps, schema_editor):
    """Create the `role_based_access_control` switch if it does not already exist."""
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.update_or_create(name=ROLE_BASED_ACCESS_CONTROL_SWITCH, defaults={'active': False})


def delete_switch(apps, schema_editor):
    """Delete the `role_based_access_control` switch."""
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.filter(name=ROLE_BASED_ACCESS_CONTROL_SWITCH).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0022_remove_role_based_access_control_switch'),
        ('enterprise_data_roles', '0002_add_enterprise_data_feature_roles'),
        ('waffle', '0001_initial')
    ]

    operations = [
        migrations.RunPython(create_switch, delete_switch),
    ]
