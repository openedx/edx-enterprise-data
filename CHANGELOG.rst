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
[10.10.1] - 2025-03-18
---------------------
  * fix: Updated FROM email address to a provisioned email address.

[10.10.0] - 2025-02-24
---------------------
  * feat: Added separate handling for of SFTP transmission failures.

[10.9.2] - 2025-03-11
---------------------
  * feat: support flex groups in csv report on LPR.

[10.9.0] - 2025-02-24
---------------------
  * feat: get groups data from membership endpoint using enterprise client.

[10.8.1] - 2025-02-20
---------------------
  * fix: Limited accuracy of floating pointing numbers to 2 places.

[10.8.1] - 2025-02-20
---------------------
  * feat: Added 2 new columns in module performance report model and exposed them via associated REST API.

[10.7.8] - 2025-02-18
---------------------
  * chore: bump version from 10.7.7 to 10.7.8 for dependency upgrades

[10.7.7] - 2025-02-11
---------------------
  * chore: upgrade python requirements

[10.7.6] - 2025-02-03
---------------------
  * chore: upgrade python requirements

[10.7.5] - 2025-01-28
---------------------
  * chore: upgrade python requirements

[10.7.4] - 2025-01-27
---------------------
  * Fix: added UTC timezone in last_updated_date in enterprise enrollments API

[10.7.3] - 2025-01-21
---------------------
  * Fix: added timestampt in last_updated_date in enterprise enrollments API

[10.7.2] - 2025-01-16
---------------------
  * Fixed duplicate entries for groups in enterprise groups API

[10.7.1] - 2025-01-07
---------------------
  * feat: add group_membership table
  * feat: add APIs to support LPR filtering for enterprise groups

[10.7.0] - 2024-12-24
---------------------
  * feat: Added user's first and last name in the enterprise enrollments API and related DB table.

[10.6.1] - 2024-12-10
---------------------
  * feat: add course_title in top courses in enrollments csv

[10.6.0] - 2024-12-09
---------------------
  * chore: upgrade python requirements

[10.5.1] - 2024-11-14
---------------------
  * chore: upgrade python requirements

[10.5.0] - 2024-11-14
---------------------
  * Fix CSV file names
  * Fix ordering of skills charts data

[10.4.0] - 2024-11-14
---------------------
  * Updated text for null emails record of leaderboard.

[10.3.0] - 2024-11-13
---------------------
  * Re-write top 10 charts queries for Enrollments, Engagements and Completions

[10.2.0] - 2024-11-12
---------------------
  * Fixed null email issue for leaderboard.


[10.1.0] - 2024-10-29
---------------------
  * Added management command to pre-warm analytics data.

[10.0.1] - 2024-10-25
---------------------
  * Same as ``10.0.0``
  * Bumping the version so a new tag can be created in the GitHub

[10.0.0] - 2024-10-25
---------------------
  * feat!: Python 3.12 Upgrade
  * Dropped support for ``Python<3.12``

[9.7.0] - 2024-10-23
---------------------
  * feat: Add API to fetch enterprise budgets information

[9.6.0] - 2024-10-14
---------------------
  * feat: Added caching for API endpoints related to advanced analytics.

[9.5.2] - 2024-10-14
---------------------
  * feat: Transform extensions_requested field to return 0 if None

[9.5.1] - 2024-10-07
---------------------
  * fix: Added handling for edge cases while fetching data from database.

[9.5.0] - 2024-10-07
---------------------
  * feat: Remove audit data filtering

[9.4.1] - 2024-10-03
---------------------
  * fix: Added guard against empty data in leaderboard queries.

[9.4.0] - 2024-09-30
---------------------
  * chore: upgrade python requirements
  * pin astriod and edx-lint packages

[9.3.0] - 2024-09-30
---------------------
  * refactor: Further improvement in SQL queries for leaderboard API endpoint.

[9.2.2] - 2024-09-27
---------------------
  * fix: remove the cache logging on EnterpriseLearnerEnrollmentViewSet.

[9.2.1] - 2024-09-25
---------------------
  * fix: Added temporary cache logging on EnterpriseLearnerEnrollmentViewSet.

[9.2.0] - 2024-09-25
---------------------
  * refactor: Performance optimizations for leaderboard API endpoints

[9.1.1] - 2024-09-24
---------------------
  * fix: disable caching for EnterpriseLearnerEnrollmentViewSet

[9.1.0] - 2024-09-23
---------------------
  * refactor: Performance optimizations for engagement and completions related API endpoints.

[9.0.1] - 2024-09-23
---------------------
  * revert: Revert "feat!: Python 3.12 Upgrade"

[8.13.0] - 2024-09-23
---------------------
  * feat: convert the skills pandas code into sql queries for better performance

[8.12.1] - 2024-09-16
---------------------
  * fix: Remove hyphens from enterprise customer UUID before database query.

[8.12.0] - 2024-09-06
---------------------
  * refactor: Performance optimizations for enrollments related API endpoints.

[8.11.1] - 2024-08-29
---------------------
  * fix: Fixed a datetime conversion error appearing on production.

[8.11.0] - 2024-08-29
---------------------
  * perf: Performance enhancements for admin analytics aggregates endpoint.

[8.10.0] - 2024-08-27
---------------------
  * feat: Added API endpoints for advance analytics engagements data.

[8.9.0] - 2024-08-23
---------------------
  * chore: Added logging to measure time taken for different code blocks.

[8.8.2] - 2024-08-16
---------------------
  * fix: typo

[8.8.1] - 2024-08-16
---------------------
  * refactor: Add logs and time measurements for different code blocks

[8.8.0] - 2024-08-15
---------------------
  * feat: Add API endpoints for advance analytics leaderboard data
  * refactor: Use `response_type` and `chart_type` in advance analytics enrollments API endpoints

[8.7.0] - 2024-08-13
---------------------
  * feat: add endpoints to get completion data for an enterprise customer

[8.6.1] - 2024-08-12
---------------------
  * Dependency updates

[8.6.0] - 2024-08-12
---------------------
  * Added API endpoints for advance analytics enrollments data.

[8.5.0] - 2024-08-12
---------------------
  * Added a new model and REST endpoint to get Exec Ed LC Module Performance data.

[8.4.0] - 2024-08-09
---------------------
  * feat: endpoint to get skills aggregated data for an enterprise customer

[8.3.1] - 2024-08-06
---------------------
  * Dependency updates

[8.3.0] - 2024-07-25
---------------------
  * refactor: Refactor code to avoid error conditions.

[8.2.0] - 2024-07-25
---------------------
  * Added a new API endpoint to get admin analytics aggregated data on user enrollment and engagement.

[8.1.0] - 2024-07-22
---------------------
  * Upgrade python requirements

[8.0.0] - 2024-07-18
---------------------
  * Fix migration for EnterpriseLearnerEnrollment model

[7.0.0] - 2024-07-12
---------------------
  * Add new fields in EnterpriseLearnerEnrollment model

[6.2.3] - 2024-07-01
---------------------
  * Dependency updates

[6.2.2] - 2024-06-24
---------------------
  * Dependency updates

[6.2.1] - 2024-05-09
---------------------
  * Bump version

[6.2.0] - 2024-03-06
---------------------
  * Dropped support for ``Django<4.2``
  * Added support for ``Python 3.12``

[6.1.1] - 2024-02-22
---------------------
  * Update uuid4 regex

[6.1.0] - 2024-02-15
---------------------
  * Permanently enable streaming csv

[6.0.0] - 2024-02-13
---------------------
  * Add streaming csv support
  * Add support to avoid call to LMS for filtering enrollments

[5.5.1] - 2024-01-10
---------------------
  * Added retry mechanism for failed report deliveries.

[5.5.0] - 2023-10-19
---------------------
  * Add data export timestamp

[5.4.1] - 2023-09-22
---------------------
  * Update NullBooleanField for Django 4.2 support

[5.4.0] - 2023-09-14
---------------------
  * Add `subsidy_access_policy_display_name` field in `EnterpriseSubsidyBudget` model

[5.3.1] - 2023-09-07
---------------------
  * Exclude hashed `id` field from `EnterpriseSubsidyBudgetSerializer`

[5.3.0] - 2023-09-07
---------------------
  * Added model and api for new policy/budget aggregates - EnterpriseSubsidyBudget


[5.0.0] - 2023-08-22
---------------------
  * Rename `summary` to `learner_engagement` in `EnterpriseLearnerEnrollmentViewSet` response


[4.11.2] - 2023-08-18
---------------------
  * Fix offer id filtering in `EnterpriseLearnerEnrollmentViewSet`


[4.11.1] - 2023-08-17
---------------------
  * Add api filtering for `EnterpriseLearnerEnrollmentViewSet` for course_title or user_email


[4.11.0] - 2023-08-16
---------------------
  * Add api endpoint for `EnterpriseAdminLearnerProgress` and `EnterpriseAdminSummarizeInsights` models


[4.10.0] - 2023-08-02
---------------------
  * Add `EnterpriseAdminLearnerProgress` and `EnterpriseAdminSummarizeInsights` models


[4.9.0] - 2023-07-20
---------------------
  * Support added for Django 4.2


[4.8.1] - 2023-07-14
---------------------
  *  Sort enterprise enrollments by default on last_activity_date.


[4.8.0] - 2023-07-4
---------------------
  * Added new fields for offer utilization in OCM and Exec-Ed product types.


[4.7.0] - 2023-06-20
---------------------
  * Added new fields for subsidy and product_line in EnterpriseLearnerEnrollmentViewSet.


[4.6.10] - 2023-06-20
---------------------
  * Improve querries and implement caching for EnterpriseLearnerEnrollmentViewSet.

[4.6.9] - 2023-06-14
--------------------
  * Allow querying of offers by either new style UUIDs or old style enterprise ID numbers.

[4.6.8] - 2023-06-14
--------------------
  * Add to_internal_value method for offer_id translation.

[4.6.7] - 2023-06-14
--------------------
  * Add support for offer_id to be either an integer or a UUID.

[4.6.6] - 2023-06-12
--------------------
  * Migrate offer_id to a varchar field in the EnterpriseOffer and EnterpriseLearnerEnrollment models.

[4.6.5] - 2023-06-09
--------------------
  * Releasing a backlog of dependency upgrades and bug fixes.

[4.6.4] - 2022-10-19
--------------------
  * Refactor enterprise api client and view filters to use cache key without user and remove dependency on session.

[4.6.3] - 2022-09-28
--------------------
  * Fixed get_enterprise_customer URL.

[4.6.2] - 2022-09-28
--------------------
  * Added logging for Enterprise API client for better debugging.


[4.6.1] - 2022-07-12
--------------------
  * Revert 4.6.0.

[4.6.0] - 2022-08-11
--------------------
  * Update primary key field in `EnterpriseLearnerEnrollment` to be `primary_key` from `enterprise_enrollment_id`.

[4.5.1] - 2022-07-12
--------------------
  * Replace `self.client` in `EnterpriseCatalogAPIClient` with `self._load_data` to account for OAuth client changes in enterprise_reporting.

[4.5.0] - 2022-06-30
--------------------
  * Add optional `ignore_null_course_list_price` query parameter to filter out enrollment records that have been refunded.

[4.4.0] - 2022-06-23
---------------------
  * Replace EdxRestApiClient with OAuthAPIClient.

[4.3.2] - 2022-06-23
--------------------
  * fix: use EnterpriseReportingModelManager for EnterpriseOffer

[4.3.1] - 2022-06-22
--------------------
  * Bump version

[4.3.0] - 2022-06-22
--------------------
  * Add `EnterpriseOffer` and `EnterpriseOfferViewSet` for offers aggregation data

[4.2.9] - 2022-06-15
---------------------
  * Add `offer_id` to `EnterpriseLearnerEnrollment`

[4.2.8] - 2022-06-15
---------------------
  * Added tests for `EnterpriseLearnerEnrollment.total_learning_time_seconds` field.

[4.2.7] - 2022-06-14
---------------------
  * Fixed issue with `total_learning_time_seconds` field in EnterpriseLearnerEnrollment

[4.2.6] - 2022-06-09
---------------------
  * Add `total_learning_time_seconds` field in EnterpriseLearnerEnrollment

[4.2.5] - 2022-04-22
---------------------
  * Rename base class to a more appropriate name
  * Remove `viewsets.ViewSet` from base class

[4.2.4] - 2022-04-18
---------------------
  * Make API endpoints readonly.

[4.2.3] - 2022-03-16
---------------------
  * Remove error handling for rate limit exceptions for data API calls

[4.2.2] - 2022-03-16
---------------------
  * Update error handling for rate limit exceptions. Moved handling to source of errors.

[4.2.1] - 2022-03-15
---------------------
  * Added error handling for rate limit exceptions

[4.2.0] - 2022-03-15
---------------------
  * Removed currently broken admin url inclusion from enterprise-data.

[4.1.2] - 2022-03-06
---------------------
  * Created a new management command for adding dummy EnterpriseLearner and EnterpriseLearnerEnrollment data for learner progress report v1.

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
