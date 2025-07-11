"""
Constants for admin analytics app.
"""

from enum import Enum


class CourseType(Enum):
    """Course type choices"""
    OCM = "OCM"
    EXECUTIVE_EDUCATION = "Executive Education"


class ResponseType(Enum):
    """Response type choices"""
    JSON = 'json'
    CSV = 'csv'
