"""Advanced Analytics Constants"""

from enum import Enum


class Granularity(Enum):
    """Granularity choices"""
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    QUARTERLY = 'Quarterly'


class Calculation(Enum):
    """Calculation choices"""
    TOTAL = 'Total'
    RUNNING_TOTAL = 'Running Total'
    MOVING_AVERAGE_3_PERIOD = 'Moving Average (3 Period)'
    MOVING_AVERAGE_7_PERIOD = 'Moving Average (7 Period)'


class EnrollmentChart(Enum):
    """CSV choices"""
    ENROLLMENTS_OVER_TIME = 'enrollments_over_time'
    TOP_COURSES_BY_ENROLLMENTS = 'top_courses_by_enrollments'
    TOP_SUBJECTS_BY_ENROLLMENTS = 'top_subjects_by_enrollments'
    INDIVIDUAL_ENROLLMENTS = 'individual_enrollments'


class ResponseType(Enum):
    """Response type choices"""
    JSON = 'json'
    CSV = 'csv'
