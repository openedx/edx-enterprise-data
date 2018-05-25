# -*- coding: utf-8 -*-
"""
Database models for enterprise data.
"""
from __future__ import absolute_import, unicode_literals

from logging import getLogger

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

LOGGER = getLogger(__name__)


@python_2_unicode_compatible
class EnterpriseEnrollment(models.Model):
    """
    Enterprise Enrollment is the learner details for a specific course enrollment.

    This information includes a mix of the learners meta data (email, username, etc), the enterprise they are
    associated with (enterprise_id, enterprise_name, etc), and their status in the course (course_id,
    letter_grade, has_passed, etc)

    This is meant to closely mirror the data the Enterprises recieve in the automated report (see enterprise_reporting
    folder in this repo), with the exception of some data that is only calculated in Vertica as this data is pulled from
    the analytics result store via the analytics-data-api project
    """

    class Meta:
        app_label = 'enterprise_data'
        db_table = 'enterprise_enrollment'
        verbose_name = _("Enterprise Enrollment")
        verbose_name_plural = _("Enterprise Enrollments")

    enterprise_id = models.UUIDField()
    enterprise_name = models.CharField(max_length=255)
    lms_user_id = models.PositiveIntegerField()
    enterprise_user_id = models.PositiveIntegerField()
    course_id = models.CharField(max_length=255, help_text='The course the learner is enrolled in.')
    enrollment_created_timestamp = models.DateTimeField()
    user_current_enrollment_mode = models.CharField(max_length=32)
    consent_granted = models.BooleanField(default=False)
    letter_grade = models.CharField(max_length=32, null=True)
    has_passed = models.BooleanField(default=False)
    passed_timestamp = models.DateTimeField(null=True)
    enterprise_sso_uid = models.CharField(max_length=255, null=True)
    enterprise_site_id = models.PositiveIntegerField(null=True)
    course_title = models.CharField(max_length=255, null=True)
    course_start = models.DateTimeField(null=True)
    course_end = models.DateTimeField(null=True)
    course_pacing_type = models.CharField(max_length=32, null=True)
    course_duration_weeks = models.CharField(max_length=32, null=True)
    course_min_effort = models.PositiveIntegerField(null=True)
    course_max_effort = models.PositiveIntegerField(null=True)
    user_account_creation_timestamp = models.DateTimeField(null=True)
    user_email = models.CharField(max_length=255, null=True)
    user_username = models.CharField(max_length=255, null=True)
    course_key = models.CharField(max_length=255, null=True)

    def __str__(self):
        """
        Return a human-readable string representation of the object.
        """
        return "<Enterprise Enrollment for user {user} in {course}>".format(
            user=self.enterprise_user_id,
            course=self.course_id
        )

    def __repr__(self):
        """
        Return uniquely identifying string representation.
        """
        return self.__str__()
