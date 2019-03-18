"""
Django rules for enterprise data
"""
from __future__ import absolute_import

import logging

import rules

logger = logging.getLogger(__name__)


@rules.predicate
def has_data_api_django_group_access(user, obj):
    """
    Returns whether the user belongs to `enterprise_data_api_access` group.
    """
    return True


rules.add_perm(
    'enterprise_data.can_view_learner_completed_courses',
    has_data_api_django_group_access | rules.predicates.is_staff
)
