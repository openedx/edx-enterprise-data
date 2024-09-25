"""
Constants for admin analytics app.
"""

from enum import Enum


class ResponseType(Enum):
    """Response type choices"""
    JSON = 'json'
    CSV = 'csv'
