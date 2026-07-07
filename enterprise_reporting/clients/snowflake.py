"""
Client for connecting to a Snowflake database.
"""

import datetime
import logging
from types import SimpleNamespace

from django.conf import settings

LOGGER = logging.getLogger(__name__)

try:
    import snowflake.connector as _snowflake_connector
except ImportError:  # pragma: no cover
    _snowflake_connector = None

_snowflake = SimpleNamespace(connector=_snowflake_connector)

try:
    from cryptography.hazmat.backends import default_backend as _default_backend
    from cryptography.hazmat.primitives import serialization as _serialization
except ImportError:  # pragma: no cover
    _default_backend = None  # type: ignore[assignment]
    _serialization = None  # type: ignore[assignment]


def _get_snowflake_connection():
    """
    Open and return a Snowflake connection using private-key authentication.

    Credentials are read from Django settings.  Required settings:
    ``SNOWFLAKE_SERVICE_USER``, ``SNOWFLAKE_SERVICE_PRIVKEY``,
    ``SNOWFLAKE_SERVICE_PASSPHRASE``.

    Raises:
        ImportError: When snowflake-connector-python is not installed.
        ValueError: When required credential settings are absent.
    """
    if _snowflake.connector is None:
        raise ImportError("snowflake-connector-python is required")

    user = getattr(settings, "SNOWFLAKE_SERVICE_USER", None)
    key_pem = getattr(settings, "SNOWFLAKE_SERVICE_PRIVKEY", None)
    passphrase = getattr(settings, "SNOWFLAKE_SERVICE_PASSPHRASE", None)
    account = getattr(settings, "SNOWFLAKE_ACCOUNT", "edx.us-east-1")
    role = getattr(settings, "SNOWFLAKE_ROLE", "ENTERPRISE_SERVICE_USER_ROLE")

    if not user:
        raise ValueError("SNOWFLAKE_SERVICE_USER must be configured")
    if not key_pem:
        raise ValueError("SNOWFLAKE_SERVICE_PRIVKEY must be configured")
    if not passphrase:
        raise ValueError("SNOWFLAKE_SERVICE_PASSPHRASE must be configured")

    key_data = key_pem.encode() if isinstance(key_pem, str) else key_pem
    private_key = _serialization.load_pem_private_key(
        key_data,
        password=passphrase.encode() if isinstance(passphrase, str) else passphrase,
        backend=_default_backend(),
    )
    private_key_bytes = private_key.private_bytes(
        encoding=_serialization.Encoding.DER,
        format=_serialization.PrivateFormat.PKCS8,
        encryption_algorithm=_serialization.NoEncryption(),
    )
    return _snowflake.connector.connect(
        user=user,
        account=account,
        private_key=private_key_bytes,
        role=role,
    )


class SnowflakeClient:
    """
    Client for connecting to Snowflake using private-key authentication.

    Credentials (private-key PEM and passphrase) are read from Django settings
    by the module-level ``_get_snowflake_connection`` factory.  Required settings:
    ``SNOWFLAKE_SERVICE_USER``, ``SNOWFLAKE_SERVICE_PRIVKEY``,
    ``SNOWFLAKE_SERVICE_PASSPHRASE``.
    """

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """
        Open a connection to Snowflake.
        """
        self.connection = _get_snowflake_connection()
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
                    formatted_row.append(value.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    formatted_row.append(value)
            yield formatted_row
