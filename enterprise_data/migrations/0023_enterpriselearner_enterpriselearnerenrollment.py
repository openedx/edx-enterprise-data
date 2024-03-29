# Generated by Django 2.2.17 on 2021-06-02 10:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enterprise_data', '0022_remove_role_based_access_control_switch'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnterpriseLearner',
            fields=[
                ('enterprise_user_id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('enterprise_customer_uuid', models.UUIDField(db_index=True)),
                ('enterprise_user_created', models.DateTimeField(null=True)),
                ('enterprise_user_modified', models.DateTimeField(null=True)),
                ('enterprise_user_active', models.BooleanField(default=False)),
                ('lms_user_id', models.PositiveIntegerField()),
                ('is_linked', models.BooleanField(default=False)),
                ('user_username', models.CharField(max_length=255, null=True)),
                ('user_email', models.CharField(db_index=True, max_length=255, null=True)),
                ('lms_user_created', models.DateTimeField(null=True)),
                ('lms_last_login', models.DateTimeField(null=True)),
                ('lms_user_country', models.CharField(max_length=2, null=True)),
                ('enterprise_sso_uid', models.CharField(max_length=255, null=True)),
                ('last_activity_date', models.DateField(db_index=True, null=True)),
                ('created_at', models.DateTimeField(db_index=True, null=True)),
            ],
            options={
                'verbose_name': 'Enterprise Learner',
                'verbose_name_plural': 'Enterprise Learner',
                'db_table': 'enterprise_learner',
            },
        ),
        migrations.CreateModel(
            name='EnterpriseLearnerEnrollment',
            fields=[
                ('enterprise_enrollment_id', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('enrollment_id', models.PositiveIntegerField(null=True)),
                ('is_consent_granted', models.BooleanField(default=False)),
                ('paid_by', models.CharField(max_length=128, null=True)),
                ('user_current_enrollment_mode', models.CharField(max_length=32)),
                ('enrollment_date', models.DateField()),
                ('unenrollment_date', models.DateField(null=True)),
                ('unenrollment_end_within_date', models.DateField(null=True)),
                ('is_refunded', models.BooleanField(default=None, null=True)),
                ('seat_delivery_method', models.CharField(max_length=128, null=True)),
                ('offer_name', models.CharField(max_length=255, null=True)),
                ('offer_type', models.CharField(max_length=128, null=True)),
                ('coupon_code', models.CharField(max_length=128, null=True)),
                ('coupon_name', models.CharField(max_length=128, null=True)),
                ('contract_id', models.CharField(max_length=128, null=True)),
                ('course_list_price', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('amount_learner_paid', models.DecimalField(decimal_places=2, max_digits=12, null=True)),
                ('course_key', models.CharField(db_index=True, max_length=255)),
                ('courserun_key', models.CharField(db_index=True, max_length=255)),
                ('course_title', models.CharField(db_index=True, max_length=255, null=True)),
                ('course_pacing_type', models.CharField(max_length=32, null=True)),
                ('course_start_date', models.DateField(db_index=True, null=True)),
                ('course_end_date', models.DateField(null=True)),
                ('course_duration_weeks', models.PositiveIntegerField(null=True)),
                ('course_max_effort', models.PositiveIntegerField(null=True)),
                ('course_min_effort', models.PositiveIntegerField(null=True)),
                ('course_primary_program', models.CharField(max_length=128, null=True)),
                ('course_primary_subject', models.CharField(max_length=128, null=True)),
                ('has_passed', models.BooleanField(default=False)),
                ('last_activity_date', models.DateField(db_index=True, null=True)),
                ('progress_status', models.CharField(max_length=128, null=True)),
                ('passed_date', models.DateField(null=True)),
                ('current_grade', models.FloatField(null=True)),
                ('letter_grade', models.CharField(max_length=32, null=True)),
                ('user_email', models.CharField(db_index=True, max_length=255, null=True)),
                ('user_account_creation_date', models.DateTimeField(null=True)),
                ('user_country_code', models.CharField(max_length=2, null=True)),
                ('user_username', models.CharField(max_length=255, null=True)),
                ('enterprise_name', models.CharField(db_index=True, max_length=255)),
                ('enterprise_customer_uuid', models.UUIDField(db_index=True)),
                ('enterprise_sso_uid', models.CharField(max_length=255, null=True)),
                ('created', models.DateTimeField(db_index=True, null=True)),
                ('enterprise_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='enterprise_data.EnterpriseLearner')),
            ],
            options={
                'verbose_name': 'Enterprise Learner Enrollment',
                'verbose_name_plural': 'Enterprise Learner Enrollments',
                'db_table': 'enterprise_learner_enrollment',
            },
        ),
    ]
