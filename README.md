# edx-enterprise-data
The edX Enterprise Data repo is the home to tools and products related to providing access to Enterprise related data.

This repository is currently split into 2 folders: enterprise_reporting and enterprise_data

## enterprise_data app
This django app exposes a REST api endpoint to access enterprise learner activity. The enterprise-data app is published
to pypi as a library and installed into the [edx-analytics-data-api](https://github.com/edx/edx-analytics-data-api/) project
and uses OAuth JWT authentication from [edx-drf-extensions](https://github.com/edx/edx-drf-extensions/blob/4569b9bf7e54a917d4acdd545b10c058c960dd1a/edx_rest_framework_extensions/auth/jwt/authentication.py#L17).

## Prerequisites for develpment
* [LMS](https://github.com/edx/devstack)
* [edx-analytics-data-api](https://github.com/edx/edx-analytics-data-api/)

## Setup for local development
This app is meant to be installed as an app in [edx-analytics-data-api](https://github.com/edx/edx-analytics-data-api/).
1. Create a directory in your filesystem that has the `edx-analytics-data-api` repo in it. Create a folder `src`, and clone this repo into the `src` directory.
1. Complete the setup in the README of `edx-analytics-data-api`
1. Navigate to `edx-analytics-data-api` and activate your virtualenv.
1. In the `edx-analytics-data-api` folder, run `make requirements`
1. Run `pip install -e ./src/edx-enterprise-data`
1. Run `./manage.py runserver`

## Frontend
Much of the data from this app is consumed by [frontend-app-learner-portal](https://github.com/edx/frontend-app-admin-portal/).
Follow the instructions in that README to set it up.

Management commands for creating development data are below.

### Management Commands for Devs

For the convenience of creating some test data in a local setup, there are some management commands that exist.
To create a test enterprise, go into the [lms shell][LMS](https://github.com/edx/devstack) and run `./manage.py lms seed_enterprise_devstack_data`
You can then use the test enterprise's UUID for the following commands.

These commands can be run from this repo or from `edx-analytics-data-api`.

To create an EnterpriseUser with a EnterpriseCustomer UUID of your choice, you can run the following:

```
$ ./manage.py create_enterprise_user <YOUR_UUID_HERE>
```

The management command uses a faker factory to fill the attributes of the object created in your DB, and will print out a command on the command line you can run if you want to add EnterpriseEnrollments for the user.

To create an EnterpriseEnrollment for an EnterpriseUser with a certain `enterprise_user_id` (that also shares the same EnterpriseCustomer UUID as an EnterpriseUser in your DB), you can run the following:

```
$ ./manage.py create_enterprise_enrollment <YOUR_UUID_HERE> <YOUR_ENTERPRISE_USER_ID_HERE>
```

To create 10 users, each with 5 enrollments, using faked data. Running multiple times will create more users and enrollments.
```
./manage.py create_dummy_data <YOUR ENTERPRISE_UUID>
```

## enterprise_reporting scripts
This folder contains a set of scripts used to push enterprise data reports.
It supports multiple delivery methods (email, sftp) and is triggered through jenkins scheduled jobs.


## enterprise_data_roles app
This app contains user roles and role assignments to manage user permissions on resources.
