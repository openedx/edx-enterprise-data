"""Mock data for enrollments"""

import pandas as pd

from enterprise_data.admin_analytics.constants import EnrollmentChart
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
        "passed_date": '2022-08-24',
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
        "passed_date": "2022-08-24",
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
        "passed_date": "2022-08-20",
        "has_passed": 0,
    },
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


def enrollments_dataframe():
    """Return a DataFrame of enrollments."""
    enrollments = pd.DataFrame(ENROLLMENTS)

    enrollments['enterprise_enrollment_date'] = enrollments['enterprise_enrollment_date'].astype('datetime64[ns]')
    enrollments['date_certificate_awarded'] = enrollments['date_certificate_awarded'].astype('datetime64[ns]')
    enrollments['date_certificate_created_raw'] = enrollments['date_certificate_created_raw'].astype('datetime64[ns]')
    enrollments['passed_date_raw'] = enrollments['passed_date_raw'].astype('datetime64[ns]')
    enrollments['passed_date'] = enrollments['passed_date'].astype('datetime64[ns]')

    return enrollments


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
