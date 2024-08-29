"""
Utility functions for interacting with the database.
"""
from contextlib import closing
from logging import getLogger

from mysql.connector import connect

from django.conf import settings

from enterprise_data.utils import timeit

LOGGER = getLogger(__name__)


def get_db_connection(database=settings.ENTERPRISE_REPORTING_DB_ALIAS):
    """
    Get a connection to the database.

    Returns:
        (mysql.connector.connection.MySQLConnection): The database connection.
    """
    return connect(
        host=settings.DATABASES[database]['HOST'],
        port=settings.DATABASES[database]['PORT'],
        database=settings.DATABASES[database]['NAME'],
        user=settings.DATABASES[database]['USER'],
        password=settings.DATABASES[database]['PASSWORD'],
    )


@timeit
def run_query(query, params: dict = None):
    """
    Run a query on the database and return the results.

    Arguments:
        query (str): The query to run.
        params (dict): The parameters to pass to the query.

    Returns:
        (list): The results of the query.
    """
    try:
        with closing(get_db_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query, params=params)
                return cursor.fetchall()
    except Exception:
        LOGGER.exception(f'[run_query]: run_query failed for query "{query}".')
        raise
