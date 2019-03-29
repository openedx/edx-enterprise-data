# edx-enterprise-data
The edX Enterprise Data repo is the home to tools and products related to providing access to Enterprise related data.

This repository is currently split into 2 folders: enterprise_reporting and enterprise_data

## enterprise_data app
This django app exposes a REST api endpoint to access enterprise learner activity. The enterprise-data app is published
to pypi as a library and installed into the [edx-analytics-data-api](https://github.com/edx/edx-analytics-data-api/) project
and uses OAuth JWT authentication from [edx-drf-extensions](https://github.com/edx/edx-drf-extensions/blob/4569b9bf7e54a917d4acdd545b10c058c960dd1a/edx_rest_framework_extensions/auth/jwt/authentication.py#L17).

### Management Commands for Devs

For the convenience of creating some test data in a local setup, there are some management commands that exist.

To create an EnterpriseUser with a EnterpriseCustomer UUID of your choice, you can run the following:

```
$ ./manage.py create_enterprise_user <YOUR_UUID_HERE>
```

The management command uses a faker factory to fill the attributes of the object created in your DB, and will print out a command on the command line you can run if you want to add EnterpriseEnrollments for the user.

To create an EnterpriseEnrollment for an EnterpriseUser with a certain `enterprise_user_id` (that also shares the same EnterpriseCustomer UUID as an EnterpriseUser in your DB), you can run the following:

```
$ ./manage.py create_enterprise_enrollment <YOUR_UUID_HERE> <YOUR_ENTERPRISE_USER_ID_HERE>
```

## enterprise_reporting scripts
This folder contains a set of scripts used to push enterprise data reports.
It supports multiple delivery methods (email, sftp) and is triggered through jenkins scheduled jobs.


## enterprise_data_roles app
This app contains user roles and role assignments to manage user permissions on resources.
