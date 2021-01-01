#!/usr/bin/env python



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

def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.
    Returns a list of requirement strings.
    """
    requirements = set()
    for path in requirements_paths:
        with open(path) as reqs:
            requirements.update(
                line.split('#')[0].strip() for line in reqs
                if is_requirement(line.strip())
            )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, a URL, or an included file.
    """
    return line and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


setup(
    name="edx-enterprise-data",
    version=VERSION,
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.8',
    ],
    description="""Enterprise Reporting""",
    author="edX",
    author_email="oscm@edx.org",
    url="https://github.com/edx/edx-enterprise-data",
    packages=[
        'enterprise_data',
        'enterprise_reporting',
        'enterprise_data_roles',
    ],
    include_package_data=True,
    install_requires=load_requirements('requirements/base.in'),
    extras_require={'reporting':load_requirements('requirements/reporting.in')},
    license="AGPL 3.0",
    zip_safe=False,
)
