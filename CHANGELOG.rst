Change Log
==========

..
   All enhancements and patches to edx-enteprise-data will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
----------

[0.2.15] - 2018-10-15
---------------------
* Add sorting for /learner_completed_courses endpoint.

[0.2.14] - 2018-10-15
---------------------
* Add sorting for /users endpoint

[0.2.13] - 2018-10-15
---------------------
* Add `progress_v2` report generation in `JSON` format

[0.2.12] - 2018-10-08
---------------------
* Add filter `all_enrollments_passed` to filter out enterprise learners on the basis of all enrollments passed
* Add extra field `course_completion_count` in response when "extra_fields" query param has value `course_completion_count`

[0.2.11] - 2018-09-28
---------------------
* Running make upgrade and installing new packages

[0.2.10] - 2018-09-28
---------------------
* Update EnterpriseUser and EnterpriseLearnerCompletedCourses viewset/serializers to ignore enrollments without content for calculations

[0.2.9] - 2018-09-24
--------------------
* Update the course catalog CSV flat file to have only one single header and a line of rows in JSON form.
* Adding filters for Learner Activity cards. These include:
    - Active learners in past week.
    - Inactive learners in past week.
    - Inactive learners in past month

[0.2.8] - 2018-09-12
--------------------
* Adding query params on /users/ enpoint for active_courses and enrollment_count

[0.2.7] - 2018-09-12
--------------------
* Add query param to get learners passed in last week
* Add support to get number of completed courses against each learner.

[0.2.6] - 2018-08-29
--------------------
* Adding EnterpriseUser endpoint support (serializer/viewset/url)
* Adding ForeignKey relationship between EnterpriseEnrollment and EnterpriseUser
* Updating some tox-battery requirements

[0.2.5] - 2018-08-28
--------------------
* Switching permission model to require enterprise_data_api_access group access
* Updated requirement versions

[0.2.4] - 2018-08-09
--------------------
* Enable ordering for all model fields in `EnterpriseEnrollmentsViewSet`.

[0.2.3] - 2018-08-07
--------------------
* Fixed migrations for enterprise_user table

[0.2.2] - 2018-08-06
--------------------
* Upgrade Django version to 1.11.15

[0.2.1] - 2018-08-1
* Add support to get last_updated_date of enterprise enrollments
* Allow api access to enrollments without pagination using `?no_page=true` query parameter
* Add .json fixture files to manifest and published package

[0.2.0] - 2018-07-31
--------------------
* Add additional authorization check to enterprise data api endpoint.

[0.1.9] - 2018-07-13
--------------------
* Add support for sorting in the `enrollments` endpoint.
* Fix broken link in `README`.

[0.1.8] - 2018-06-29
--------------------
* Introduce endpoint for returning summary data about enterprise enrollments.

[0.1.7] - 2018-06-28
--------------------
* Make the enterprise enrollment schema match the field changes made in the pipeline.

[0.1.2 - 0.1.3] - 2018-05-01
----------------------------
* Clean up field name discrepancy for `enterprise_site_id` and `user_account_creation_timestamp`

[0.1.1] - 2018-04-30
--------------------
* Add `enterprise_site_id` to response and align `enterprise_sso_uid` with the proper field from the pipeline.


[0.1.0] - 2018-03-07
--------------------

* Add new app `enterprise_api`. This django app is used to expose a REST endpoint in th eex-analytics-data-api project.
