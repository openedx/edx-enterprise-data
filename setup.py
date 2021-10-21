#!/usr/bin/env python



import os
import re
import sys

from setuptools import setup

# groups "my-package-name<=x.y.z,..." into ("my-package-name", "<=x.y.z,...")
requirement_line_regex = re.compile(r"([a-zA-Z0-9-]+)([<>=][^#\s]+)?")

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
    Load all requirements from the specified requirements files, including any constraints from other files that
    are pulled in.
    Returns a list of requirement strings.
    """
    requirements = {}
    constraint_files = set()

    def add_version_constraint_or_raise(current_line, current_requirements, add_if_not_present):
        regex_match = requirement_line_regex.match(current_line)
        if regex_match:
            package = regex_match.group(1)
            version_constraints = regex_match.group(2)
            existing_version_constraints = current_requirements.get(package, None)
            # it's fine to add constraints to an unconstrained package, but raise an error if there are already
            # constraints in place
            if existing_version_constraints and existing_version_constraints != version_constraints:
                raise BaseException('Multiple constraint definitions found for {}: "{}" and "{}".'
                                    .format(package, existing_version_constraints, version_constraints))
            if add_if_not_present or package in current_requirements:
                current_requirements[package] = version_constraints

    # process .in files and store the path to any constraint files that are pulled in
    for path in requirements_paths:
        with open(path) as reqs:
            for line in reqs:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, True)
                # ignore non-local constraint files
                if line and line.startswith('-c') and not line.startswith('-c http'):
                    constraint_files.add(os.path.dirname(path) + '/' + line.split('#')[0].replace('-c', '').strip())

    # process constraint files and add any new constraints found to existing requirements
    for constraint_file in constraint_files:
        with open(constraint_file) as reader:
            for line in reader:
                if is_requirement(line):
                    add_version_constraint_or_raise(line, requirements, False)

    # process back into list of "pkg><=constraints" strings
    return ['{}{}'.format(pkg, version or '') for (pkg, version) in requirements.items()]


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement;
    that is, it is not blank, a comment, a URL, or an included file.
    """
    return line and line.strip() and not line.startswith(('-r', '#', '-e', 'git+', '-c'))


setup(
    name="edx-enterprise-data",
    version=VERSION,
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Programming Language :: Python :: 3',
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
