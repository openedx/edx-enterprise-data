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

=======
[1.2.6] - 2019-05-13
--------------------
* Clean up rbac authorization related waffle switche OFF logic.

[1.2.5] - 2019-05-06
--------------------
* Version upgrade for edx-rbac.

[1.2.4] - 2019-04-22
--------------------
* Use `get_decoded_jwt_from_request` from edx-rbac.

[1.2.3] - 2019-04-22
--------------------
* Version upgrade of edx-rbac.

[1.2.2] - 2019-04-16
--------------------
* Turn on role base access control switch.

[1.2.1] - 2019-04-07
--------------------
* Update role base permission checks

[1.2.0] - 2019-03-29
--------------------
* Moved feature role models to a separate django app.

[1.1.0] - 2019-03-26
--------------------
* Initial implementation of RBAC logic in viewsets and filters, behind a waffle switch.

[1.0.18] - 2019-03-19
---------------------
* Add feature role models for permission based checks

[1.0.17] - 2019-03-05
---------------------
* In audit enrollments filtering, only filter out audit rows that do not have any offer or code applied.

[1.0.16] - 2019-01-24
--------------------
* Respect the "externally managed" data consent policy in the enrollment view.

[1.0.15] - 2019-01-24
---------------------
* Bumping version so others can install newer version of this app that includes convenient management commands for devs
* Includes create_enterprise_user, create_enterprise_enrollment management commands for creating demo test data for local development

[1.0.12] - 2018-11-05
--------------------
* Only include current active enrollments which are not complete yet in active learners table.

[1.0.11] - 2018-11-02
--------------------
Revert 1.0.9 changes - enrollment_created_date as this value is redundent with the enrollment_created_timestamp

[1.0.10] - 2018-11-02
--------------------
Upgrade dependencies

[1.0.9] - 2018-11-02
--------------------
* Add "enrollment_created_date" to progress report

[1.0.8] - 2018-10-29
--------------------
* Enable audit enrollments filtering on field `user_current_enrollment_mode` for model `EnterpriseEnrollment`

[1.0.7] - 2018-10-25
--------------------
* Fixed KeyError issue when PGP Encryption key is not found

[1.0.6] - 2018-10-25
--------------------
* Updating enrollment_count and course_completion_count computations to restrict to consent_granted=True enrollments

[1.0.5] - 2018-10-25
--------------------
* Ability to PGP encrypt report files sent via email and SFTP

[1.0.4] - 2018-10-24
--------------------
* Updating packages

[1.0.3] - 2018-10-24
--------------------
* Tweaking a outeref call for course_completion_count computation

[1.0.2] - 2018-10-24
--------------------
* Fixing bug with course_completion_count computation

[1.0.1] - 2018-10-23
--------------------
* Making enterprise_user endpoint sortable on enrollment_count and course_completion_count

[1.0.0] - 2018-10-16
--------------------
* Updated edx-drf-extensions imports. edx-enterprise-data will no longer work
  with outdated versions of edx-drf-extensions.

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

* Add new app `enterprise_api`. This django app is used to expose a REST endpoint in the edx-analytics-data-api project.
