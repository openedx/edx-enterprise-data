# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-03-24 11:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0022_remove_role_based_access_control_switch'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnterpriseSubsectionGrade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enterprise_id', models.UUIDField()),
                ('enterprise_name', models.CharField(max_length=255)),
                ('user_email', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('lms_user_id', models.PositiveIntegerField()),
                ('course_id', models.CharField(max_length=255)),
                ('section_block_id', models.CharField(max_length=564)),
                ('section_display_name', models.CharField(max_length=255)),
                ('section_index', models.PositiveIntegerField()),
                ('subsection_block_id', models.CharField(max_length=564)),
                ('subsection_display_name', models.CharField(max_length=255)),
                ('subsection_index', models.PositiveIntegerField()),
                ('subsection_grade_created', models.DateTimeField(null=True)),
                ('first_attempted', models.DateTimeField(null=True)),
                ('earned_all', models.FloatField()),
                ('possible_all', models.FloatField()),
                ('earned_graded', models.FloatField()),
                ('possible_graded', models.FloatField()),
                ('enterprise_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subsection_grades', to='enterprise_data.EnterpriseUser', to_field='enterprise_user_id')),
            ],
            options={
                'db_table': 'enterprise_subsection_grade',
            },
        ),
    ]
