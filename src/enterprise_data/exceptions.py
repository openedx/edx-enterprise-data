"""
Custom Exceptions related to enterprise data.
"""


class EnterpriseDataException(Exception):
    """
    Base exception for enterprise data.
    """

    def __init__(self, message: str):
        """
        Initialize the exception with a message.
        """
        super().__init__(message)


class EnterpriseApiClientException(EnterpriseDataException):
    """
    Exception for enterprise API client.
    """
