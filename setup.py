#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import os
import re
import sys

from setuptools import setup


def get_version(*file_paths):
    """
    Extract the version string from the file at the given relative path fragments.
    """
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

VERSION = get_version("enterprise_data", "__init__.py")

if sys.argv[-1] == "tag":
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (VERSION, VERSION))
    os.system("git push --tags")
    sys.exit()

base_path = os.path.dirname(__file__)

REQUIREMENTS = open(os.path.join(base_path, 'requirements', 'base.txt')).read().splitlines()

setup(
    name="edx-enterprise-data",
    version=VERSION,
    description="""Enterprise Reporting""",
    author="edX",
    author_email="oscm@edx.org",
    url="https://github.com/edx/edx-enterprise-data",
    packages=[
        'enterprise_data',
        'enterprise_reporting'
    ],
    include_package_data=True,
    install_requires=REQUIREMENTS,
    license="AGPL 3.0",
    zip_safe=False,
)
