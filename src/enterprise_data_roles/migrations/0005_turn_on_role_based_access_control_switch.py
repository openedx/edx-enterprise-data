from django.db import migrations

from enterprise_data_roles.constants import ROLE_BASED_ACCESS_CONTROL_SWITCH


def turn_on_switch(apps, schema_editor):
    """Turn on the `role_based_access_control` switch."""
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.update_or_create(name=ROLE_BASED_ACCESS_CONTROL_SWITCH, defaults={'active': True})


def turn_off_switch(apps, schema_editor):
    """Turn off the the `role_based_access_control` switch."""
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.update_or_create(name=ROLE_BASED_ACCESS_CONTROL_SWITCH, defaults={'active': False})


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data_roles', '0004_enterprisedataroleassignment_enterprise_id'),
    ]

    operations = [
        migrations.RunPython(turn_on_switch, turn_off_switch),
    ]
