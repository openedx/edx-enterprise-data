"""
Query filter for between operation.
"""
from .base import QueryFilter


class INQueryFilter(QueryFilter):
    """
    Query filter for IN operation.
    """

    def __init__(self, column: str, values: list = None, values_placeholders: list = None):
        """
        Initialize the filter.

        This will also validate arguments.
        """
        self.validate_argument_exclusivity(values, values_placeholders)

        self.column = column
        self.values = values
        self.values_placeholders = values_placeholders

    def to_sql(self) -> str:
        if self.values is not None:
            value_str = f"({', '.join(repr(v) for v in self.values)})"
            return f"{self.column} IN {value_str}"
        else:
            placeholders = ', '.join(f"%({item})s" for item in self.values_placeholders)
            return f"{self.column} IN ({placeholders})"
