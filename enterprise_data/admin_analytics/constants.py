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


class ResponseType(Enum):
    """Response type choices"""
    JSON = 'json'
    CSV = 'csv'
