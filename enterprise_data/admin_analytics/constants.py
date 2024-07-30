"""
Constants for admin analytics.
"""
import mysql.connector

from django.conf import settings

DATABASE_CONNECTION_CONFIG = {
    'host': settings.DATABASES[settings.ENTERPRISE_REPORTING_DB_ALIAS]['HOST'],
    'port': settings.DATABASES[settings.ENTERPRISE_REPORTING_DB_ALIAS]['PORT'],
    'database': settings.DATABASES[settings.ENTERPRISE_REPORTING_DB_ALIAS]['NAME'],
    'user': settings.DATABASES[settings.ENTERPRISE_REPORTING_DB_ALIAS]['USER'],
    'password': settings.DATABASES[settings.ENTERPRISE_REPORTING_DB_ALIAS]['PASSWORD'],
}
DATABASE_CONNECTOR = mysql.connector.connect
