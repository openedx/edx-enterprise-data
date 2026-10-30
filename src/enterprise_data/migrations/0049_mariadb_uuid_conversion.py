# Generated migration for MariaDB UUID field conversion (Django 5.2)
"""
Migration to convert UUIDField from char(32) to uuid type for MariaDB compatibility.
"""

from django.db import migrations


def apply_mariadb_migration(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        if 'mariadb' not in version.lower():
            return
    with connection.cursor() as cursor:
        # EnterpriseEnrollment
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY enterprise_customer_uuid uuid NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY budget_id uuid NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY subscription_license_uuid uuid NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY enterprise_group_uuid uuid NULL")
        # EnterpriseUser
        cursor.execute("ALTER TABLE enterprise_data_enterpriseuser MODIFY enterprise_customer_uuid uuid NOT NULL")
        # EnterpriseOffer
        cursor.execute("ALTER TABLE enterprise_data_enterpriseoffer MODIFY enterprise_customer_uuid uuid NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseoffer MODIFY enterprise_id uuid NOT NULL")
        # EnterpriseBudget
        cursor.execute("ALTER TABLE enterprise_data_enterprisebudget MODIFY enterprise_customer_uuid uuid NOT NULL")
        # EnterpriseSubsidyBudget
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY subsidy_access_policy_uuid uuid NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY subsidy_uuid uuid NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY enterprise_customer_uuid uuid NOT NULL")
        # EnterpriseLearner
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_customer_id uuid NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_group_uuid uuid NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_group_membership_uuid uuid NULL")
        # EnterpriseSubsidyTransaction
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY enterprise_id uuid NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY subsidy_transaction_id uuid NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY enterprise_customer_uuid uuid NULL")


def reverse_mariadb_migration(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        if 'mariadb' not in version.lower():
            return
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY enterprise_customer_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY budget_id char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY subscription_license_uuid char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseenrollment MODIFY enterprise_group_uuid char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseuser MODIFY enterprise_customer_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseoffer MODIFY enterprise_customer_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriseoffer MODIFY enterprise_id char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisebudget MODIFY enterprise_customer_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY subsidy_access_policy_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY subsidy_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidybudget MODIFY enterprise_customer_uuid char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_customer_id char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_group_uuid char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterpriselearner MODIFY enterprise_group_membership_uuid char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY enterprise_id char(32) NOT NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY subsidy_transaction_id char(32) NULL")
        cursor.execute("ALTER TABLE enterprise_data_enterprisesubsidytransaction MODIFY enterprise_customer_uuid char(32) NULL")


class Migration(migrations.Migration):
    dependencies = [
        ('enterprise_data', '0048_alter_enterpriseexecedlcmoduleperformance_avg_after_lo_score_and_more'),
    ]
    operations = [
        migrations.RunPython(
            code=apply_mariadb_migration,
            reverse_code=reverse_mariadb_migration,
        ),
    ]
