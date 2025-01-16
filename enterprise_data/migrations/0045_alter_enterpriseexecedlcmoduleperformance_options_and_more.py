# Generated by Django 4.2.15 on 2024-12-23 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0044_enterpriseexecedlcmoduleperformance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='enterpriseexecedlcmoduleperformance',
            options={'verbose_name': 'Exec Ed LC Module Performance', 'verbose_name_plural': 'Exec Ed LC Module Performance'},
        ),
        migrations.AddField(
            model_name='enterpriselearnerenrollment',
            name='user_first_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='enterpriselearnerenrollment',
            name='user_last_name',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
