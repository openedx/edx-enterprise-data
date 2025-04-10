"""
Query filter for equal operation.
"""
from .base import QueryFilter


class EqualQueryFilter(QueryFilter):
    """
    Query filter for equal operation.
    """
    def __init__(self, column: str, value: str = None, value_placeholder: str = None):
        """
        Initialize the filter.

        This will also validate arguments.
        """
        self.validate_argument_exclusivity(value, value_placeholder)

        self.column = column
        self.value = value
        self.value_placeholder = value_placeholder

    def to_sql(self) -> str:
        if self.value is not None:
            return f'{self.column} = {self.value_to_sql(self.value)}'
        else:
            return f'{self.column} = %({self.value_placeholder})s'
