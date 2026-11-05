from django.db import migrations

from enterprise_data_roles.constants import ENTERPRISE_DATA_ADMIN_ROLE


def create_roles(apps, schema_editor):
    """Create the enterprise data roles if they do not already exist."""
    EnterpriseDataFeatureRole = apps.get_model('enterprise_data', 'EnterpriseDataFeatureRole')
    EnterpriseDataFeatureRole.objects.update_or_create(name=ENTERPRISE_DATA_ADMIN_ROLE)


def delete_roles(apps, schema_editor):
    """Delete the enterprise data roles."""
    EnterpriseDataFeatureRole = apps.get_model('enterprise_data', 'EnterpriseDataFeatureRole')
    EnterpriseDataFeatureRole.objects.filter(name=ENTERPRISE_DATA_ADMIN_ROLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0018_enterprisedatafeaturerole_enterprisedataroleassignment'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles)
    ]
