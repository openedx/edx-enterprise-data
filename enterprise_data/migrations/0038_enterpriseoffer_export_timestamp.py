# Generated by Django 3.2.20 on 2023-10-19 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0037_alter_enterpriseenrollment_consent_granted'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterpriseoffer',
            name='export_timestamp',
            field=models.DateTimeField(null=True),
        ),
    ]
