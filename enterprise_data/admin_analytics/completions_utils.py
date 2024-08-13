"""This module contains utility functions for completions analytics."""
from enterprise_data.utils import date_filter


def date_aggregation(level, group, date, df, type_="count"):
    """Perform date aggregation on a DataFrame.

    This function aggregates data based on the specified level of aggregation (e.g., daily, weekly, monthly, quarterly)
    and returns the aggregated data.

    Args:
        level (str): The level of aggregation. Possible values are "Daily", "Weekly", "Monthly", and "Quarterly".
        group (list): A list of column names to group the data by.
        date (str): The name of the date column in the DataFrame.
        df (pandas.DataFrame): The DataFrame containing the data to be aggregated.
        type_ (str, optional): The type of aggregation to perform. Possible values
            are "count" and "sum". Defaults to "count".

    Returns:
        pandas.DataFrame: The aggregated data.

    """
    if type_ == "count":
        if level == "Daily":
            df = df.groupby(group).size().reset_index()
            group.append("count")
            df.columns = group
        elif level == "Weekly":
            df[date] = df[date].dt.to_period("W").dt.start_time
            df = df.groupby(group).size().reset_index()
            group.append("count")
            df.columns = group
        elif level == "Monthly":
            df[date] = df[date].dt.to_period("M").dt.start_time
            df = df.groupby(group).size().reset_index()
            group.append("count")
            df.columns = group
        elif level == "Quarterly":
            df[date] = df[date].dt.to_period("Q").dt.start_time
            df = df.groupby(group).size().reset_index()
            group.append("count")
            df.columns = group
    elif type_ == "sum":
        if level == "Daily":
            df = df.groupby(group).sum().reset_index()
            group.append("sum")
            df.columns = group
        elif level == "Weekly":
            df[date] = df[date].dt.to_period("W").dt.start_time
            df = df.groupby(group).sum().reset_index()
            group.append("sum")
            df.columns = group
        elif level == "Monthly":
            df[date] = df[date].dt.to_period("M").dt.start_time
            df = df.groupby(group).sum().reset_index()
            group.append("sum")
            df.columns = group
        elif level == "Quarterly":
            df[date] = df[date].dt.to_period("Q").dt.start_time
            df = df.groupby(group).sum().reset_index()
            group.append("sum")
            df.columns = group

    return df


def calculation(calc, df, type_="count"):
    """Perform a calculation on the given DataFrame based on the specified calculation type.

    Args:
        calc (str): The calculation type. Possible values are "Total", "Running Total",
                    "Moving Average (3 Period)", and "Moving Average (7 Period)".
        df (pandas.DataFrame): The filtered enrollments data.
        type_ (str, optional): The type of calculation to perform. Default is "count".

    Returns:
        pandas.DataFrame: The aggregated data after performing the calculation.
    """
    if type_ == "count":
        if calc == "Total":
            pass
        elif calc == "Running Total":
            df["count"] = df.groupby("enroll_type")["count"].cumsum()
        elif calc == "Moving Average (3 Period)":
            df["count"] = (
                df.groupby("enroll_type")["count"]
                .rolling(3)
                .mean()
                .droplevel(level=[0])
            )
        elif calc == "Moving Average (7 Period)":
            df["count"] = (
                df.groupby("enroll_type")["count"]
                .rolling(7)
                .mean()
                .droplevel(level=[0])
            )
    elif type_ == "sum":
        if calc == "Total":
            pass
        elif calc == "Running Total":
            df["sum"] = df.groupby("enroll_type")["sum"].cumsum()
        elif calc == "Moving Average (3 Period)":
            df["sum"] = (
                df.groupby("enroll_type")["sum"].rolling(3).mean().droplevel(level=[0])
            )
        elif calc == "Moving Average (7 Period)":
            df["sum"] = (
                df.groupby("enroll_type")["sum"].rolling(7).mean().droplevel(level=[0])
            )

    return df


def get_completions_over_time(start_date, end_date, dff, date_agg, calc):
    """Get agreggated data for completions over time graph.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        dff (pandas.DataFrame): enrollments data
        date_agg (str): It denotes the granularity of the aggregated date which can be Daily, Weekly, Monthly, Quarterly
        calc (str): Calculations denoiated the period for the running averages. It can be Total, Running Total, Moving
            Average (3 Period), Moving Average (7 Period)
    """

    dff = dff[dff["has_passed"] == 1]

    # Date filtering.
    dff = date_filter(start=start_date, end=end_date, data_frame=dff, date_column="passed_date")

    # Date aggregation.
    dff = date_aggregation(
        level=date_agg, group=["passed_date", "enroll_type"], date="passed_date", df=dff
    )

    # Calculating metric.
    dff = calculation(calc=calc, df=dff)

    return dff


def get_top_courses_by_completions(start_date, end_date, dff):
    """Get top 10 courses by completions.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        dff (pandas.DataFrame): Enrollments data
    """

    dff = dff[dff["has_passed"] == 1]

    # Date filtering.
    dff = date_filter(start=start_date, end=end_date, data_frame=dff, date_column="passed_date")

    courses = list(
        dff.groupby(["course_key"]).size().sort_values(ascending=False)[:10].index
    )

    dff = (
        dff[dff.course_key.isin(courses)]
        .groupby(["course_key", "course_title", "enroll_type"])
        .size()
        .reset_index()
    )
    dff.columns = ["course_key", "course_title", "enroll_type", "count"]

    return dff


def get_top_subjects_by_completions(start_date, end_date, dff):
    """Get top 10 subjects by completions.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        dff (pandas.DataFrame): Enrollments data
    """

    dff = dff[dff["has_passed"] == 1]

    # Date filtering.
    dff = date_filter(start=start_date, end=end_date, data_frame=dff, date_column="passed_date")

    subjects = list(
        dff.groupby(["course_subject"]).size().sort_values(ascending=False)[:10].index
    )

    dff = (
        dff[dff.course_subject.isin(subjects)]
        .groupby(["course_subject", "enroll_type"])
        .size()
        .reset_index()
    )
    dff.columns = ["course_subject", "enroll_type", "count"]

    return dff


def get_csv_data_for_completions_over_time(
    start_date, end_date, enrollments, date_agg, calc
):
    """Get csv data for completions over time graph.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        enrollments (pandas.DataFrame): Filtered enrollments data
        date_agg (str): it denotes the granularity of the aggregated date which can be Daily, Weekly, Monthly, Quarterly
        calc (str): calculations denoiated the period for the running averages. It can be Total, Running Total, Moving
            Average (3 Period), Moving Average (7 Period)

    Returns:
        dict: csv data
    """

    dff = get_completions_over_time(start_date, end_date, enrollments, date_agg, calc)
    dff = dff.pivot(index="passed_date", columns="enroll_type", values="count")
    filename = (
        f"Completions Timeseries, {start_date} - {end_date} ({date_agg} {calc}).csv"
    )
    return {"filename": filename, "data": dff}


def get_csv_data_for_top_courses_by_completions(start_date, end_date, enrollments):
    """Get csv data for top 10 courses by completions.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        enrollments (pandas.DataFrame): Filtered enrollments data

    Returns:
        dict: csv data
    """

    dff = get_top_courses_by_completions(start_date, end_date, enrollments)
    dff = dff.pivot(
        index=["course_key", "course_title"], columns="enroll_type", values="count"
    )
    filename = f"Top 10 Courses by Completions, {start_date} - {end_date}.csv"
    return {"filename": filename, "data": dff}


def get_csv_data_for_top_subjects_by_completions(start_date, end_date, enrollments):
    """Get csv data for top 10 subjects by completions.

    Args:
        start_date (datetime): The start date for the date filter.
        end_date (datetime): The end date for the date filter.
        enrollments (pandas.DataFrame): Filtered enrollments data

    Returns:
        dict: csv data
    """

    dff = get_top_subjects_by_completions(start_date, end_date, enrollments)
    dff = dff.pivot(index="course_subject", columns="enroll_type", values="count")
    filename = f"Top 10 Subjects by Completions, {start_date} - {end_date}.csv"
    return {"filename": filename, "data": dff}
