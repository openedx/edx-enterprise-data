"""
Base class to store the table information.
"""


class BaseTable:
    """
    Singleton class to store the table information.
    """
    instance = None

    def __new__(cls):
        """
        Singleton method to create a single instance of the table.
        """
        if cls.instance is None:
            cls.instance = super(BaseTable, cls).__new__(cls)
        return cls.instance
