"""
Client for connecting to a Snowflake database.
"""

import datetime
import os
from logging import getLogger

from snowflake import connector

LOGGER = getLogger(__name__)


class SnowflakeClient:
    """
    Client for connecting to Snowflake.
    """

    def __init__(self, username=None, password=None, account=None):
        """
        Instantiate a new client using the Django settings to determine the Snowflake credentials.
        If there are none configured, throw an exception.
        """
        username = username or os.environ['SNOWFLAKE_USERNAME']
        password = password or os.environ['SNOWFLAKE_PASSWORD']
        account = account or os.environ['SNOWFLAKE_ACCOUNT']

        self.connection_info = {
            'user': username,
            'password': password,
            'account': account,
        }

        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Open a connection to Snowflake.
        """
        self.connection = connector.connect(**self.connection_info)
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """
        Close the connection to Snowflake.
        """
        self.cursor.close()
        self.connection.close()
        self.cursor = None
        self.connection = None

    def stream_results(self, query):
        """
        Streams the results for a query using the current connection.
        """
        for row in self.cursor.execute(query):
            formatted_row = []
            for value in row:
                if isinstance(value, datetime.datetime):
                    formatted_row.append(value.strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    formatted_row.append(value)
            yield formatted_row
