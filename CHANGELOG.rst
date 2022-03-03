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

=========================
[4.1.1] - 2022-03-01
---------------------
  * Created a new management command for adding EnterpriseLearnerEnrollment dummy data for learner progress report v1.

[4.1.0] - 2022-03-01
---------------------
  * Created a new management command for adding dummy data for learner progress report v1.

[4.0.0] - 2022-02-14
---------------------
  * Dropped support for Django 2.2, 3.0 and 3.1

[3.3.0] - 2021-09-21
---------------------
  * Added support for Django32

[3.2.0] - 2021-09-17
---------------------
  * Add api gateway spec for LPR V1 API

[3.1.0] - 2021-09-16
---------------------
  * add `primary_program_type` field in EnterpriseLearnerEnrollment
  * update max_length value for existing fields in EnterpriseLearnerEnrollment

[3.0.0] - 2021-09-07
---------------------
* Remove old field names from LPR API V1
* Maintain same field order for `progress_v3` csv generated from `admin-portal` and `enterprise_reporting`

[2.2.21] - 2021-08-31
---------------------
* Pass old and new fields in LPR API V1 response for EnterpriseLearnerViewSet and EnterpriseLearnerEnrollmentViewSet
* Update csv header for EnterpriseLearnerViewSet and EnterpriseLearnerEnrollmentViewSet APIs
* Add support for `progress_v3` enterprise report

[2.2.20] - 2021-08-13
---------------------
* Add ref_name to the same named serializers in v0 and v1 of enterprise data

[2.2.19] - 2021-08-04
---------------------
* Include `has_passed` field in API V1 response

[2.2.18] - 2021-07-27
---------------------
* Include all fields in Analytics API V1 response

[2.2.17] - 2021-07-15
---------------------
* Update the edx-rbac from 1.3.3 to 1.5.0

[2.2.16] - 2021-07-09
--------------------
* Revert changes made in 2.2.15

[2.2.15] - 2021-07-08
--------------------
* Update default database selection for Analytics API V1
* Update filter backend queryset for Audit enrollments

[2.2.14] - 2021-07-07
--------------------
* Update logs

[2.2.13] - 2021-07-06
--------------------
* Database query updates

[2.2.12] - 2021-07-04
--------------------
* Database query optimizations for API V1

[2.2.11] - 2021-07-02
--------------------
* Add more logging and remove filter backend

[2.2.10] - 2021-07-02
--------------------
* Add logging and update queryset logic

[2.2.9] - 2021-07-01
--------------------
* Remove `EnterpriseReportingLinkedUserModelManager`

[2.2.8] - 2021-06-07
--------------------
* Rename API V1 endpoint name from `learners` to `users`

[2.2.7] - 2021-06-02
--------------------
* Alter model field type from Decimal to Float

[2.2.6] - 2021-06-02
--------------------
* Add enterprise_enrollment_id as primary key on EnterpriseLearnerEnrollment model

[2.2.5] - 2021-06-01
--------------------
* Update API V1
* Updated API V1 Serializers
* Updated API V1 Model Field Types

[2.2.4] - 2021-05-31
--------------------
* Fix incorrect model field name

[2.2.3] - 2021-05-31
--------------------
* Update API V1 model constraints

[2.2.2] - 2021-05-28
--------------------
* API V1 model changes

[2.2.1] - 2021-05-28
--------------------
* Fix model field in query

[2.2.0] - 2021-05-26
--------------------
* New v1 API to leverage Snowflake powered analytics

[2.1.5] - 2021-03-10
--------------------
* Updated S3 Object locations for Pearson reports.

[2.1.4] - 2021-01-07
--------------------
* added `engagement` in DATA_TYPES.

[2.1.3] - 2020-10-09
--------------------
* Removed ``python_2_unicode_compatible`` decorator.

[2.1.2] - 2020-09-03
--------------------
* Added custom pagination to increase page_size limit of Enterprise Enrollments API

[2.1.0] - 2020-05-05
--------------------
* Updates factories to create more dummy data
* Adds course and date filters to the enrollment view
* Updates README with installation instructions

[2.1.0] - 2020-05-05
--------------------
* Upgrade python packages.
* Add support for python 3.8

[2.0.0] - 2020-04-01
--------------------
* Fix for JWT being double encoded
* Drop python 2.7 support
* Add support to Django 2.0, 2.1 and 2.2

[1.3.16] - 2020-03-13
---------------------
* Fix compatibility warnings with Django2.0. Remove support for Django<1.9,
* Upgrade python packages.

[1.3.15] - 2020-03-10
---------------------
* Added enterprise learner engagement report.

[1.3.14] - 2020-03-06
---------------------
* Upgrade python packages. Using requirements/base.in to load requirements.
* Package requirements of enterprise_reporting scripts are declared as extra requirements.

[1.3.13] - 2020-01-20
---------------------
* added support of `search` query param in EnterpriseEnrollmentsViewSet.

[1.3.12] - 2019-12-31
---------------------
* Update edx-rbac.

[1.3.11] - 2019-12-27
---------------------
* Added the ability to include or exclude date from reporting configuration file name.

[1.3.10] - 2019-12-11
---------------------
* Added the correct condition for logging the warning in enterprise-enrollments endpoint.

[1.3.9] - 2019-12-03
---------------------
* Requests package upgraded from 2.9.1 to 2.22.0.

[1.3.8] - 2019-11-19
---------------------
* Removed the `NotFound` exception in enterprise-enrollments endpoint.

[1.3.7] - 2019-09-20
---------------------
* Upgrade python packages.

[1.3.6] - 2019-09-20
---------------------
* Update changelog.

[1.3.5] - 2019-09-19
---------------------
* Fix zip password decryption for sftp delivery.

[1.3.4] - 2019-09-06
---------------------
* Replaced `has_passed` field in enrollments API with `progress_status`.

[1.3.3] - 2019-08-22
---------------------
* Fixed issue where same day un-enrollment is shown as `FALSE` in `unenrollment_end_within_date` column of learner report.

[1.3.2] - 2019-08-09
---------------------
* Do not apply encrypted version of password on zipfile in enterprise reporting.

[1.3.1] - 2019-08-06
---------------------
* Make zipfile password protected with encrypted_password in enterprise reporting.

[1.3.0] - 2019-07-15
---------------------
* Replce edx-rbac jwt utils with edx-drf-extensions jwt utils

[1.2.13] - 2019-07-10
---------------------
* Add logging to monitor enterprise data api.

[1.2.12] - 2019-06-18
---------------------
* Pin edx-rbac to 0.2.1 and other package upgrades.

[1.2.11] - 2019-06-17
---------------------
* filtering audit enrollment records based on Enterprise customer's enable_audit_data_reporting instead of enable_audit_enrollment

[1.2.10] - 2019-06-04
---------------------
* Pin edx-opaque-keys to 0.4.4 to avoid dependency conflicts downstream.

[1.2.9] - 2019-05-28
--------------------
* Fallback to request.auth if JWT cookies are not found.

[1.2.8] - 2019-05-17
--------------------
* Remove RBAC switch from DB.

[1.2.7] - 2019-05-13
--------------------
* Replace edx_rbac.utils.get_decoded_jwt_from_request with edx_rest_framework_extensions.auth.jwt.cookies.get_decoded_jwt.

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
