"""
Client for connecting to a Vertica database.
"""


import datetime
import os
from logging import getLogger

import vertica_python

LOGGER = getLogger(__name__)


class VerticaClient:
    """
    Client for connecting to Vertica.
    """

    def __init__(self, host=None, username=None, password=None):
        """
        Instantiate a new client using the Django settings to determine the vertica credentials.
        If there are none configured, throw an exception.
        """
        self.connection_info = {
            'host': host or os.environ.get('VERTICA_HOST'),
            'user': username or os.environ.get('VERTICA_USERNAME'),
            'password': password or os.environ.get('VERTICA_PASSWORD'),
            'database': 'warehouse',
        }

        self.connection = None

    def connect(self):
        """
        Open a connection to Vertica.
        """
        self.connection = vertica_python.connect(**self.connection_info)

    def close_connection(self):
        """
        Close the connection to vertica.
        """
        self.connection.close()
        self.connection = None

    def stream_results(self, query):
        """
        Streams the results for a query using the current connection.
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        for row in cursor.iterate():
            formatted_row = []
            for value in row:
                if isinstance(value, datetime.datetime):
                    formatted_row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    formatted_row.append(value)
            yield formatted_row

    def fetch_results(self, query):
        """
        Fetches all of the results for a query using the current connection.
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
