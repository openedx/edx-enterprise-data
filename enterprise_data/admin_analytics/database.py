"""
Utility functions for interacting with the database.
"""
from contextlib import closing
from logging import getLogger

from enterprise_data.admin_analytics.constants import DATABASE_CONNECTION_CONFIG, DATABASE_CONNECTOR
from enterprise_data.utils import timeit

LOGGER = getLogger(__name__)


@timeit
def run_query(query):
    """
    Run a query on the database and return the results.

    Arguments:
        query (str): The query to run.

    Returns:
        (list): The results of the query.
    """
    try:
        with closing(DATABASE_CONNECTOR(**DATABASE_CONNECTION_CONFIG)) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
    except Exception:
        LOGGER.exception(f'[run_query]: run_query failed for query "{query}".')
        raise
