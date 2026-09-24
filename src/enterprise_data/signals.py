# pylint: skip-file

"""
Signals for enterprise-data.
"""


from edx_django_utils.cache import TieredCache

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from enterprise_data.models import EnterpriseLearner, EnterpriseLearnerEnrollment
from enterprise_data.utils import get_cache_key


@receiver([post_save, post_delete], sender=[EnterpriseLearner, EnterpriseLearnerEnrollment])
def clear_cache(instance, **kwargs):
    """
    Signal receiver function to clear the cache of specified model.
    """
    cache_key = get_cache_key(
        resource='enterprise-learner',
        enterprise_customer=instance.enterprise_customer_uuid,
    )
    TieredCache.delete_all_tiers(cache_key)


# connecting signal with reciever.
post_save.connect(clear_cache, sender=EnterpriseLearner)
post_save.connect(clear_cache, sender=EnterpriseLearnerEnrollment)
post_delete.connect(clear_cache, sender=EnterpriseLearner)
post_delete.connect(clear_cache, sender=EnterpriseLearnerEnrollment)
