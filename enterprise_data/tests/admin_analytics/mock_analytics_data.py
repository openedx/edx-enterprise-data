"""Mock data for enrollments"""

import pandas as pd

from enterprise_data.admin_analytics.constants import EngagementChart, EnrollmentChart
from enterprise_data.admin_analytics.utils import ChartType

ENROLLMENTS = [
    {
        "enterprise_customer_name": "Hill Ltd",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "lms_enrollment_id": 1013,
        "user_id": 8907,
        "email": "rebeccanelson@example.com",
        "course_key": "hEmW+tvk03",
        "courserun_key": "course-v1:hEmW+tvk03+1T9889",
        "course_id": "1681",
        "course_subject": "business-management",
        "course_title": "Re-engineered tangible approach",
        "enterprise_enrollment_date": "2021-07-04",
        "lms_enrollment_mode": "verified",
        "enroll_type": "certificate",
        "program_title": "Non-Program",
        "date_certificate_awarded": "2021-08-25",
        "grade_percent": 0.99,
        "cert_awarded": 1,
        "date_certificate_created_raw": "2021-08-25",
        "passed_date_raw": "2021-08-25",
        "passed_date": "2021-08-25",
        "has_passed": 1,
    },
    {
        "enterprise_customer_name": "Hill Ltd",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "lms_enrollment_id": 9172,
        "user_id": 8369,
        "email": "taylorjames@example.com",
        "course_key": "hEmW+tvk03",
        "courserun_key": "course-v1:hEmW+tvk03+1T9889",
        "course_id": "1681",
        "course_subject": "business-management",
        "course_title": "Re-engineered tangible approach",
        "enterprise_enrollment_date": "2021-07-03",
        "lms_enrollment_mode": "verified",
        "enroll_type": "certificate",
        "program_title": "Non-Program",
        "date_certificate_awarded": "2021-09-01",
        "grade_percent": 0.93,
        "cert_awarded": 1,
        "date_certificate_created_raw": "2021-09-01",
        "passed_date_raw": "2021-09-01",
        "passed_date": "2021-09-01",
        "has_passed": 1,
    },
    {
        "enterprise_customer_name": "Hill Ltd",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "lms_enrollment_id": 9552,
        "user_id": 8719,
        "email": "ssmith@example.com",
        "course_key": "qZJC+KFX86",
        "courserun_key": "course-v1:qZJC+KFX86+1T8918",
        "course_id": "1725",
        "course_subject": "medicine",
        "course_title": "Secured static capability",
        "enterprise_enrollment_date": "2021-05-11",
        "lms_enrollment_mode": "verified",
        "enroll_type": "certificate",
        "program_title": "Non-Program",
        "date_certificate_awarded": None,
        "grade_percent": 0.0,
        "cert_awarded": 0,
        "date_certificate_created_raw": None,
        "passed_date_raw": None,
        "passed_date": None,
        "has_passed": 0,
    },
    {
        "enterprise_customer_name": "Hill Ltd",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "lms_enrollment_id": 3436,
        "user_id": 3125,
        "email": "kathleenmartin@example.com",
        "course_key": "QWXx+Jqz64",
        "courserun_key": "course-v1:QWXx+Jqz64+1T9449",
        "course_id": "4878",
        "course_subject": "social-sciences",
        "course_title": "Horizontal solution-oriented hub",
        "enterprise_enrollment_date": "2020-04-03",
        "lms_enrollment_mode": "verified",
        "enroll_type": "certificate",
        "program_title": "Non-Program",
        "date_certificate_awarded": None,
        "grade_percent": 0.0,
        "cert_awarded": 0,
        "date_certificate_created_raw": None,
        "passed_date_raw": None,
        "passed_date": None,
        "has_passed": 0,
    },
    {
        "enterprise_customer_name": "Hill Ltd",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "lms_enrollment_id": 5934,
        "user_id": 4853,
        "email": "amber79@example.com",
        "course_key": "NOGk+UVD31",
        "courserun_key": "course-v1:NOGk+UVD31+1T4956",
        "course_id": "4141",
        "course_subject": "communication",
        "course_title": "Streamlined zero-defect attitude",
        "enterprise_enrollment_date": "2020-04-08",
        "lms_enrollment_mode": "verified",
        "enroll_type": "certificate",
        "program_title": "Non-Program",
        "date_certificate_awarded": None,
        "grade_percent": 0.0,
        "cert_awarded": 0,
        "date_certificate_created_raw": None,
        "passed_date_raw": None,
        "passed_date": None,
        "has_passed": 0,
    },
]

ENGAGEMENTS = [
    {
        "user_id": 2340,
        "email": "padillamichelle@example.org",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-08-05",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 0,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 3724,
    },
    {
        "user_id": 1869,
        "email": "yallison@example.org",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-07-27",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 0,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 4335,
    },
    {
        "user_id": 6962,
        "email": "weaverpatricia@example.net",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-08-05",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 0,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 9441,
    },
    {
        "user_id": 6798,
        "email": "seth57@example.org",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-08-21",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 1,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 9898,
    },
    {
        "user_id": 8530,
        "email": "mackwilliam@example.com",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-10-24",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 0,
        "is_engaged_video": 0,
        "is_engaged_forum": 0,
        "is_engaged_problem": 0,
        "is_active": 1,
        "learning_time_seconds": 0,
    },
    {
        "user_id": 7584,
        "email": "graceperez@example.com",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2022-05-17",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 0,
        "is_engaged_video": 0,
        "is_engaged_forum": 0,
        "is_engaged_problem": 0,
        "is_active": 1,
        "learning_time_seconds": 21,
    },
    {
        "user_id": 68,
        "email": "yferguson@example.net",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-09-02",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 0,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 4747,
    },
    {
        "user_id": 4278,
        "email": "caseyjohnny@example.com",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "Kcpr+XoR30",
        "enroll_type": "certificate",
        "activity_date": "2022-05-20",
        "course_title": "Assimilated even-keeled focus group",
        "course_subject": "engineering",
        "is_engaged": 0,
        "is_engaged_video": 0,
        "is_engaged_forum": 0,
        "is_engaged_problem": 0,
        "is_active": 1,
        "learning_time_seconds": 0,
    },
    {
        "user_id": 8726,
        "email": "webertodd@example.com",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-09-21",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 1,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 5285,
    },
    {
        "user_id": 282,
        "email": "crystal86@example.net",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-07-11",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 0,
        "is_engaged_video": 0,
        "is_engaged_forum": 0,
        "is_engaged_problem": 0,
        "is_active": 1,
        "learning_time_seconds": 0,
    },
    {
        "user_id": 2731,
        "email": "paul77@example.org",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-07-26",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 1,
        "is_engaged_video": 1,
        "is_engaged_forum": 1,
        "is_engaged_problem": 1,
        "is_active": 1,
        "learning_time_seconds": 15753,
    },
    {
        "user_id": 4038,
        "email": "samanthaclarke@example.org",
        "enterprise_customer_uuid": "33ce656295e04ecfa2a77d407eb96f69",
        "course_key": "luGg+KNt30",
        "enroll_type": "certificate",
        "activity_date": "2021-07-19",
        "course_title": "Synergized reciprocal encoding",
        "course_subject": "business-management",
        "is_engaged": 0,
        "is_engaged_video": 0,
        "is_engaged_forum": 0,
        "is_engaged_problem": 0,
        "is_active": 1,
        "learning_time_seconds": 29,
    }
]

ENROLLMENT_STATS_CSVS = {
    EnrollmentChart.ENROLLMENTS_OVER_TIME.value: (
        b'enterprise_enrollment_date,certificate\n'
        b'2020-04-03,1\n'
        b'2020-04-08,1\n'
        b'2021-05-11,1\n'
        b'2021-07-03,1\n'
        b'2021-07-04,1\n'
    ),
    EnrollmentChart.TOP_COURSES_BY_ENROLLMENTS.value: (
        b'course_key,course_title,certificate\n'
        b'NOGk+UVD31,Streamlined zero-defect attitude,1\n'
        b'QWXx+Jqz64,Horizontal solution-oriented hub,1\n'
        b'hEmW+tvk03,Re-engineered tangible approach,2\n'
        b'qZJC+KFX86,Secured static capability,1\n'
    ),
    EnrollmentChart.TOP_SUBJECTS_BY_ENROLLMENTS.value: (
        b'course_subject,certificate\nbusiness-management,2\ncommunication,1\nmedicine,1\nsocial-sciences,1\n'
    )
}

ENGAGEMENT_STATS_CSVS = {
    EngagementChart.ENGAGEMENTS_OVER_TIME.value: (
        b'activity_date,certificate\n'
        b'2021-07-19,0.0\n'
        b'2021-07-26,4.4\n'
        b'2021-07-27,1.2\n'
        b'2021-08-05,3.6\n'
        b'2021-08-21,2.7\n'
        b'2021-09-02,1.3\n'
        b'2021-09-21,1.5\n'
        b'2022-05-17,0.0\n'
    ),
    EngagementChart.TOP_COURSES_BY_ENGAGEMENTS.value: (
        b'course_key,course_title,certificate\n'
        b'Kcpr+XoR30,Assimilated even-keeled focus group,0.0\n'
        b'luGg+KNt30,Synergized reciprocal encoding,14.786944444444444\n'
    ),
    EngagementChart.TOP_SUBJECTS_BY_ENGAGEMENTS.value: (
        b'course_subject,certificate\n'
        b'business-management,14.786944444444444\n'
        b'engineering,0.0\n'
    )
}


def enrollments_dataframe():
    """Return a DataFrame of enrollments."""
    enrollments = pd.DataFrame(ENROLLMENTS)

    enrollments['enterprise_enrollment_date'] = enrollments['enterprise_enrollment_date'].astype('datetime64[ns]')
    enrollments['date_certificate_awarded'] = enrollments['date_certificate_awarded'].astype('datetime64[ns]')
    enrollments['date_certificate_created_raw'] = enrollments['date_certificate_created_raw'].astype('datetime64[ns]')
    enrollments['passed_date_raw'] = enrollments['passed_date_raw'].astype('datetime64[ns]')
    enrollments['passed_date'] = enrollments['passed_date'].astype('datetime64[ns]')

    return enrollments


def engagements_dataframe():
    """Return a DataFrame of engagements."""
    engagements = pd.DataFrame(ENGAGEMENTS)
    engagements['activity_date'] = engagements['activity_date'].astype('datetime64[ns]')
    return engagements


def enrollments_csv_content():
    """Return the CSV content of enrollments."""
    return (
        b'email,course_title,course_subject,enroll_type,enterprise_enrollment_date\r\n'
        b'rebeccanelson@example.com,Re-engineered tangible approach,business-management,certificate,2021-07-04\r\n'
        b'taylorjames@example.com,Re-engineered tangible approach,business-management,certificate,2021-07-03\r\n'
        b'ssmith@example.com,Secured static capability,medicine,certificate,2021-05-11\r\n'
        b'amber79@example.com,Streamlined zero-defect attitude,communication,certificate,2020-04-08\r\n'
        b'kathleenmartin@example.com,Horizontal solution-oriented hub,social-sciences,certificate,2020-04-03\r\n'
    )


def leaderboard_csv_content():
    """Return the CSV content of leaderboard."""
    # return (
    #     b'email,learning_time_hours,daily_sessions,average_session_length,course_completions\r\n'
    #     b'paul77@example.org,4.4,1,4.4,\r\nseth57@example.org,2.7,1,2.7,\r\n'
    #     b'weaverpatricia@example.net,2.6,1,2.6,\r\nwebertodd@example.com,1.5,1,1.5,\r\n'
    #     b'yferguson@example.net,1.3,1,1.3,\r\nyallison@example.org,1.2,1,1.2,\r\n'
    #     b'padillamichelle@example.org,1.0,1,1.0,\r\ncaseyjohnny@example.com,0.0,0,,\r\n'
    #     b'crystal86@example.net,0.0,0,,\r\ngraceperez@example.com,0.0,0,,\r\n'
    #     b'mackwilliam@example.com,0.0,0,,\r\nsamanthaclarke@example.org,0.0,0,,\r\n'
    # )

    return (
        b'email,learning_time_hours,daily_sessions,average_session_length,course_completions\r\n'
        b'paul77@example.org,4.4,1,4.4,\r\nseth57@example.org,2.7,1,2.7,\r\n'
        b'weaverpatricia@example.net,2.6,1,2.6,\r\nwebertodd@example.com,1.5,1,1.5,\r\n'
        b'yferguson@example.net,1.3,1,1.3,\r\nyallison@example.org,1.2,1,1.2,\r\n'
        b'padillamichelle@example.org,1.0,1,1.0,\r\ncaseyjohnny@example.com,0.0,0,0.0,\r\n'
        b'crystal86@example.net,0.0,0,0.0,\r\ngraceperez@example.com,0.0,0,0.0,\r\n'
        b'mackwilliam@example.com,0.0,0,0.0,\r\nsamanthaclarke@example.org,0.0,0,0.0,\r\n'
    )


LEADERBOARD_RESPONSE = [
    {
        "email": "paul77@example.org",
        "daily_sessions": 1,
        "learning_time_seconds": 15753,
        "learning_time_hours": 4.4,
        "average_session_length": 4.4,
        "course_completions": None,
    },
    {
        "email": "seth57@example.org",
        "daily_sessions": 1,
        "learning_time_seconds": 9898,
        "learning_time_hours": 2.7,
        "average_session_length": 2.7,
        "course_completions": None,
    },
    {
        "email": "weaverpatricia@example.net",
        "daily_sessions": 1,
        "learning_time_seconds": 9441,
        "learning_time_hours": 2.6,
        "average_session_length": 2.6,
        "course_completions": None,
    },
    {
        "email": "webertodd@example.com",
        "daily_sessions": 1,
        "learning_time_seconds": 5285,
        "learning_time_hours": 1.5,
        "average_session_length": 1.5,
        "course_completions": None,
    },
    {
        "email": "yferguson@example.net",
        "daily_sessions": 1,
        "learning_time_seconds": 4747,
        "learning_time_hours": 1.3,
        "average_session_length": 1.3,
        "course_completions": None,
    },
    {
        "email": "yallison@example.org",
        "daily_sessions": 1,
        "learning_time_seconds": 4335,
        "learning_time_hours": 1.2,
        "average_session_length": 1.2,
        "course_completions": None,
    },
    {
        "email": "padillamichelle@example.org",
        "daily_sessions": 1,
        "learning_time_seconds": 3724,
        "learning_time_hours": 1.0,
        "average_session_length": 1.0,
        "course_completions": None,
    },
    {
        "email": "caseyjohnny@example.com",
        "daily_sessions": 0,
        "learning_time_seconds": 0,
        "learning_time_hours": 0.0,
        "average_session_length": 0.0,
        "course_completions": None,
    },
    {
        "email": "crystal86@example.net",
        "daily_sessions": 0,
        "learning_time_seconds": 0,
        "learning_time_hours": 0.0,
        "average_session_length": 0.0,
        "course_completions": None,
    },
    {
        "email": "graceperez@example.com",
        "daily_sessions": 0,
        "learning_time_seconds": 21,
        "learning_time_hours": 0.0,
        "average_session_length": 0.0,
        "course_completions": None,
    },
    {
        "email": "mackwilliam@example.com",
        "daily_sessions": 0,
        "learning_time_seconds": 0,
        "learning_time_hours": 0.0,
        "average_session_length": 0.0,
        "course_completions": None,
    },
    {
        "email": "samanthaclarke@example.org",
        "daily_sessions": 0,
        "learning_time_seconds": 29,
        "learning_time_hours": 0.0,
        "average_session_length": 0.0,
        "course_completions": None,
    },
]

COMPLETIONS_STATS_CSVS = {
    ChartType.COMPLETIONS_OVER_TIME.value: (
        b'passed_date,certificate\n'
        b'2021-08-25,1\n'
        b'2021-09-01,2\n'
    ),
    ChartType.TOP_COURSES_BY_COMPLETIONS.value: (
        b'course_key,course_title,certificate\n'
        b'hEmW+tvk03,Re-engineered tangible approach,2\n'
    ),
    ChartType.TOP_SUBJECTS_BY_COMPLETIONS.value: (
        b'course_subject,certificate\n'
        b'business-management,2\n'
    )
}


def engagements_csv_content():
    """Return the CSV content of engagements."""
    return (
        b'email,course_title,activity_date,course_subject,learning_time_hours\r\n'
        b'graceperez@example.com,Synergized reciprocal encoding,2022-05-17,business-management,0.0\r\n'
        b'webertodd@example.com,Synergized reciprocal encoding,2021-09-21,business-management,1.5\r\n'
        b'yferguson@example.net,Synergized reciprocal encoding,2021-09-02,business-management,1.3\r\n'
        b'seth57@example.org,Synergized reciprocal encoding,2021-08-21,business-management,2.7\r\n'
        b'padillamichelle@example.org,Synergized reciprocal encoding,2021-08-05,business-management,1.0\r\n'
        b'weaverpatricia@example.net,Synergized reciprocal encoding,2021-08-05,business-management,2.6\r\n'
        b'yallison@example.org,Synergized reciprocal encoding,2021-07-27,business-management,1.2\r\n'
        b'paul77@example.org,Synergized reciprocal encoding,2021-07-26,business-management,4.4\r\n'
        b'samanthaclarke@example.org,Synergized reciprocal encoding,2021-07-19,business-management,0.0\r\n'
    )
