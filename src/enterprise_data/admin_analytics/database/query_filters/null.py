"""
Query filter for to check if a column is NULL or NOT NULL.
"""
from .base import QueryFilter


class NULLQueryFilter(QueryFilter):
    """
    Query filter for checking if a column is NULL or NOT NULL.
    """
    def __init__(self, column: str, null_check: bool):
        """
        Initialize the filter.
        """
        self.column = column
        self.null_check = null_check

    def to_sql(self) -> str:
        return f'{self.column} IS NULL' if self.null_check else f'{self.column} IS NOT NULL'
