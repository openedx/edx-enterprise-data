# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-04 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0013_auto_20180831_1931'),
    ]

    operations = [
        migrations.AddField(
            model_name='enterpriseuser',
            name='created',
            field=models.DateTimeField(null=True),
        ),
    ]
