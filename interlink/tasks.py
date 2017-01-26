# --coding: utf8--

from itertools import chain
from celery import shared_task

from django.conf import settings
from django.utils.module_loading import import_string

from interlink.models import Link


@shared_task
def handle_keyword_addition(obj):
    Link.objects.create_for_keyword(obj)


@shared_task
def handle_keyword_deletion(obj):
    donors = set(link.donor for link in Link.objects.with_keyword(obj))
    for donor in donors:
        Link.objects.create_for_donor(donor, exclude_keywords=[obj, ])


@shared_task
def generate_interlinks():
    total_links, created, skipped = 0, 0, 0
    querysets = import_string(settings.INTERLINK_QUERYSETS)
    for item in chain.from_iterable(querysets.available_objects()):
        try:
            link_count = Link.objects.create_for_donor(item)
            if link_count:
                created += 1
                total_links += link_count
            else:
                skipped += 1
        except ValueError:
            pass
    return (total_links, created, skipped)
