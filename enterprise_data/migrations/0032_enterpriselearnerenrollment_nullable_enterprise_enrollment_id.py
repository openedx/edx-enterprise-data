# Generated by Django 3.2.13 on 2022-08-11 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0031_enterpriselearnerenrollment_switch_primary_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enterpriselearnerenrollment',
            name='enterprise_enrollment_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
