"""
Query filter for comparison operations.
"""
from .base import QueryFilter


class ComparisonQueryFilter(QueryFilter):
    """
    Generic query filter for comparison operations (=, <, >, <=, >=, <>, !=).
    """

    def __init__(self, column: str, operator: str, value: str = None, value_placeholder: str = None):
        """
        Initialize the filter.

        This will also validate arguments.
        """
        if operator not in {"=", "<", ">", "<=", ">=", "<>", "!="}:
            raise ValueError(f"Invalid operator: {operator}")

        self.operator = operator
        self.validate_argument_exclusivity(value, value_placeholder)

        self.column = column
        self.value = value
        self.value_placeholder = value_placeholder

    def to_sql(self) -> str:
        if self.value is not None:
            return f"{self.column} {self.operator} {self.value_to_sql(self.value)}"
        else:
            return f"{self.column} {self.operator} %({self.value_placeholder})s"
