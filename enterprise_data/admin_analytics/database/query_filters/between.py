"""
Query filter for between operation.
"""
from .base import QueryFilter


class BetweenQueryFilter(QueryFilter):
    """
    Query filter for between operation.
    """

    def __init__(self, column: str, _range: tuple = None, range_placeholders: tuple = None):
        """
        Initialize the filter.

        This will also validate arguments.
        """
        self.validate_argument_exclusivity(_range, range_placeholders)

        self.column = column
        self.range = _range
        self.range_placeholders = range_placeholders

    def to_sql(self) -> str:
        if self.range:
            lower, upper = self.range
            return f'{self.column} BETWEEN {self.value_to_sql(lower)} AND {self.value_to_sql(upper)}'
        else:
            lower_placeholder, upper_placeholder = self.range_placeholders
            return f'{self.column} BETWEEN %({lower_placeholder})s AND %({upper_placeholder})s'
