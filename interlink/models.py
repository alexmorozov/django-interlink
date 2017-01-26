# --coding: utf8--

import logging

from collections import OrderedDict

from itertools import islice

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.template import Template, Context
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from interlink.utils import idiverse, models_of_same_type

log = logging.getLogger(__name__)


class KeywordQuerySet(models.QuerySet):
    def available_keywords_of(self, items, donor, exclude_recipients=None,
                              exclude_keywords=None):
        """
        Get all available keywords for a list of models of the same type,
        considering keywords' weights.
        """
        pk_map = OrderedDict((item.pk, item) for item in items)

        if not pk_map:
            return []

        ct = ContentType.objects.get_for_model(items[0])

        # Remove objects that link to the donor themselves to avoid
        # short-circiuting
        donor_ct = ContentType.objects.get_for_model(donor)
        reverse_donors = (Link.objects
                          .filter(keyword__content_type=donor_ct,
                                  keyword__object_id=donor.pk,
                                  content_type=ct)
                          .values_list('object_id', flat=True))
        for reverse_pk in reverse_donors:
            pk_map.pop(reverse_pk, None)

        # Make sure the donor won't link to itself
        if models_of_same_type(donor, items[0]):
            pk_map.pop(donor.pk, None)

        if exclude_recipients and models_of_same_type(exclude_recipients[0], items[0]):  # NOQA
            for item in exclude_recipients:
                pk_map.pop(item.pk, None)

        # Select keywords that haven't been used up.
        number_field = models.F('weight') - models.F('links__count')
        keywords = (self
                    .filter(content_type=ct, object_id__in=pk_map)
                    .annotate(models.Count('links'))
                    .annotate(number=number_field)
                    .filter(number__gt=0)
                    .order_by('object_id', '-number'))

        if exclude_keywords:
            keywords = keywords.exclude(
                pk__in=[x.pk for x in exclude_keywords])

        unique_by_object = {}
        for keyword in keywords:
            # Fill back the object in the keyword to avoid unnecessary queries
            keyword.content_object = pk_map[keyword.object_id]
            unique_by_object.setdefault(keyword.object_id, keyword)

        return unique_by_object.values()

    def candidates_for(self, model, exclude_recipients=None,
                       exclude_keywords=None):
        """
        Get keyword candidates for a given `model` instance to link to.

        Keep the diversity among the types of target models as high as
        possible.
        """
        querysets = import_string(settings.INTERLINK_QUERYSETS)
        candidates = querysets.relevant_objects(model)

        keywords = [
            self.available_keywords_of(objects, donor=model,
                                       exclude_recipients=exclude_recipients,
                                       exclude_keywords=exclude_keywords)
            for objects in candidates
        ]
        return islice(idiverse(keywords), settings.INTERLINK_LINKS_PER_PAGE)


class Keyword(models.Model):
    WEIGHT_CHOICES = [(x, x) for x in range(1, 4)]

    object_id = models.IntegerField(
        db_index=True)
    content_type = models.ForeignKey(
        ContentType)
    content_object = GenericForeignKey()
    text = models.CharField(
        max_length=100,
        help_text=_('Django templating supported with {{ object }} '
                    'being the current object'))
    weight = models.IntegerField(
        choices=WEIGHT_CHOICES,
        default=1,
        help_text=_('Repeat a keyword several times'))

    objects = KeywordQuerySet.as_manager()

    def __unicode__(self):
        return self.text

    def rendered_text(self):
        template = Template(self.text)
        context = Context({'object': self.content_object})
        return template.render(context)


@receiver(post_save, sender=Keyword)
def on_new_keyword(sender, instance, **kwargs):
    if kwargs['created']:
        import interlink.tasks
        interlink.tasks.handle_keyword_addition(instance)


@receiver(pre_delete, sender=Keyword)
def on_keyword_delete(sender, instance, **kwargs):
    import interlink.tasks
    interlink.tasks.handle_keyword_deletion(instance)


class LinkQuerySet(models.QuerySet):
    def outgoing(self, model):
        """
        Get all the links that a `model` instance is pointing to.
        """
        ct = ContentType.objects.get_for_model(model)
        return (self
                .filter(object_id=model.pk, content_type=ct)
                .select_related('keyword')
                .prefetch_related('donor', 'keyword__content_object'))

    def incoming(self, model):
        """
        Get all the links pointing to a `model`.
        """
        ct = ContentType.objects.get_for_model(model)
        return (self
                .filter(keyword__object_id=model.pk,
                        keyword__content_type=ct)
                .select_related('keyword')
                .prefetch_related('donor', 'keyword__content_object'))

    def with_keyword(self, keyword):
        """
        Get all the links with a specified `keyword`.
        """
        return (self
                .filter(keyword=keyword)
                .select_related('keyword')
                .prefetch_related('donor', 'keyword__content_object'))

    def only_from(self, model):
        """
        Links from a `model` instance only.
        """
        ct = ContentType.objects.get_for_model(model)
        return self.filter(object_id=model.pk, content_type=ct)

    def only_to(self, model):
        """
        Links pointing to a `model` instance only.
        """
        ct = ContentType.objects.get_for_model(model)
        return self.filter(keyword__object_id=model.pk,
                           keyword__content_type=ct)

    def create_for_donor(self, donor, exclude_recipients=None,
                         exclude_keywords=None):
        """
        Create interlinks up to the donor's link capacity.
        """
        total_slots = settings.INTERLINK_LINKS_PER_PAGE
        occupied_slots = self.outgoing(donor).count()
        free_slots = total_slots - occupied_slots
        if not free_slots:
            log.warning(
                _('The donor %s doesn\'t have free link slots') % donor)
            return 0

        keywords = islice(
            Keyword.objects.candidates_for(
                donor, exclude_recipients, exclude_keywords),
            free_slots)
        links = [Link(donor=donor, keyword=keyword, order=occupied_slots + i)
                 for i, keyword in enumerate(keywords)]
        self.bulk_create(links)

        return len(links)

    def create_for_keyword(self, keyword, exclude=None):
        """
        Create interlink(s) for a particular keyword.
        """
        recipient = keyword.content_object
        capacity = keyword.weight
        used = Link.objects.filter(keyword=keyword).count()
        free_slots = capacity - used

        querysets = import_string(settings.INTERLINK_QUERYSETS)
        candidates = querysets.relevant_objects(recipient)

        if exclude is None:
            exclude = []
        exclude.append(recipient)

        def validate(item):
            if item in exclude:
                return False
            outgoing = self.outgoing(item)
            if outgoing.count() >= settings.INTERLINK_LINKS_PER_PAGE:
                return False
            if outgoing.only_to(recipient).exists():
                return False
            if self.incoming(item).only_from(recipient).exists():
                return False
            return True

        donors = islice(idiverse(candidates, validate=validate), free_slots)

        links = [Link(donor=donor, keyword=keyword, order=used + i)
                 for i, donor in enumerate(donors)]
        self.bulk_create(links)

        return len(links)


class Link(models.Model):
    object_id = models.IntegerField(
        db_index=True)
    content_type = models.ForeignKey(
        ContentType)
    donor = GenericForeignKey()
    keyword = models.ForeignKey(
        Keyword,
        related_name='links')
    order = models.IntegerField(
        default=0)

    objects = LinkQuerySet.as_manager()

    class Meta:
        ordering = ('order', )

    def __unicode__(self):
        return u'{x.donor} => {x.keyword}'.format(x=self)
