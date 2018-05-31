# edx-enterprise-data
The edX Enterprise Data repo is the home to tools and products related to providing access to Enterprise related data.

This repository is currently split into 2 folders: enterprise_reporting and enterprise_data

## enterprise_data app
This django app exposes a REST api endpoint to access enterprise learner activity. The enterprise-data app is published
to pypi as a library and installed into the [edx-analytics-data-api](https://github.com/edx/edx-analytics-data-api/) project
and uses OAuth JWT authentication from [edx-drf-extensions](https://github.com/edx/edx-drf-extensions/blob/master/edx_rest_framework_extensions/authentication.py).

## enterprise_reporting scripts
This folder contains a set of scripts used to push enterprise data reports.
It supports multiple delivery methods (email, sftp) and is triggered through jenkins scheduled jobs.
