"""
Base Query Filter.
"""
from abc import ABC, abstractmethod


class QueryFilter(ABC):
    """
    Base Query filter class for functionality common to all filters.
    """
    @abstractmethod
    def to_sql(self) -> str:
        """
        Convert the filter to a SQL string.
        """
        raise NotImplementedError

    @staticmethod
    def validate_argument_exclusivity(value, value_placeholder):
        """
        Validate that that arguments are mutually exclusive.

        This method will make sure that at-least one of the value or value_placeholder is provided. it will also
        make sure that both value and value_placeholder are not provided at the same time.

        Arguments:
            value: The value of the filter.
            value_placeholder: The placeholder for the value.
        """
        if value is not None and value_placeholder is not None:
            raise ValueError('Both value and value_placeholder cannot be provided at the same time.')
        if value is None and value_placeholder is None:
            raise ValueError('Either value or value_placeholder must be provided.')
        return True

    def value_to_sql(self, value):
        """
        Convert the given value to a string in a way that it can be used inside WHERE clause of SQL query.

        Note: This method is meant to evolve according to user needs. currently it handles the following data types.
        More types can be added as needed.

        1. str: Encloses the string in single quotes.
        2. list<str>: Encloses the list of strings in a tuple after calling this method recursively on each item.

        Arguments:
            value (Any): The value to format.

        Returns:
            (Any): The formatted value.
        """
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, list):
            return [self.value_to_sql(item) for item in value]

        return value


class QueryFilters(list):
    """
    A list of QueryFilter objects.
    """
    def to_sql(self) -> str:
        """
        Convert the filters to a SQL string.
        """
        return ' AND '.join([_filter.to_sql() for _filter in self])
