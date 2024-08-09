"""This module contains utility functions for completions analytics."""
from enterprise_data.utils import date_filter


def date_aggregation(level, group, date, df, type_="count"):
    """Date aggregation function.

    Args:
        level (str): level of aggregation
        date (str): date column
        df (pandas.DataFrame): Filtered enrollment data
        type_ (str, optional): Defaults to "count".

    Returns:
        (pandas.DataFrame) : aggregated data
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
    """Calculation function.

    Args:
        calc (_type_): calculation type
        df (pandas.DataFrame): Filtered enrollment data

    Returns:
        (pandas.DataFrame) : aggregated data
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


def get_completions_over_time(start_date, end_date, enrollments, date_agg, calc):
    """Get agreggated data for completions over time graph."""

    dff = enrollments.copy()
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


def get_top_courses_by_completions(start_date, end_date, enrollments):
    """Get top 10 courses by completions."""

    dff = enrollments.copy()
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


def get_top_subjects_by_completions(start_date, end_date, enrollments):
    """Get top 10 subjects by completions."""

    dff = enrollments.copy()
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


def get_csv_data_for_completions_over_time(start_date, end_date, enrollments, date_agg, calc):
    """Get csv data for completions over time graph."""

    dff = get_completions_over_time(start_date, end_date, enrollments, date_agg, calc)
    dff = dff.pivot(index='passed_date', columns='enroll_type', values='count')
    filename = f"Completions Timeseries, {start_date} - {end_date} ({date_agg} {calc}).csv"
    return {"filename": filename, "data": dff}


def get_csv_data_for_top_courses_by_completions(start_date, end_date, enrollments):
    """Get csv data for top 10 courses by completions."""

    dff = get_top_courses_by_completions(start_date, end_date, enrollments)
    dff = dff.pivot(
        index=["course_key", "course_title"], columns="enroll_type", values="count"
    )
    filename = f"Top 10 Courses by Completions, {start_date} - {end_date}.csv"
    return {"filename": filename, "data": dff}


def get_csv_data_for_top_subjects_by_completions(start_date, end_date, enrollments):
    """Get csv data for top 10 subjects by completions."""

    dff = get_top_subjects_by_completions(start_date, end_date, enrollments)
    dff = dff.pivot(index="course_subject", columns="enroll_type", values="count")
    filename = f"Top 10 Subjects by Completions, {start_date} - {end_date}.csv"
    return {"filename": filename, "data": dff}
