"""
Utility functions for fetching data from the database.
"""
from logging import getLogger

import pandas

from enterprise_data.admin_analytics.database import run_query

LOGGER = getLogger(__name__)


def fetch_max_enrollment_datetime():
    """
    Fetch the latest created date from the enterprise_learner_enrollment table.

    created will be same for all records as this is added at the time of data load. Which is when the async process
    populates the data in the table. We can use this to get the latest data load time.
    """
    query = "SELECT MAX(created) FROM enterprise_learner_enrollment"
    results = run_query(query)
    if not results:
        return None
    return pandas.to_datetime(results[0][0], utc=True)
