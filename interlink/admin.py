#--coding: utf8--

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.db import models
from django.utils.translation import ugettext_lazy as _

from interlink.models import Keyword, Link


class KeywordsInline(GenericTabularInline):
    model = Keyword


class IsUsedFilter(admin.SimpleListFilter):
    title = _('Is used')
    parameter_name = 'is_used'
    YES = '1'
    NO = '0'

    def lookups(self, request, model_admin):
        return (
            (self.YES, _('Yes')),
            (self.NO, _('No')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == self.YES:
            return queryset.filter(used_times__gt=0)
        if value == self.NO:
            return queryset.filter(used_times=0)
        return queryset


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['text', 'content_object', 'weight', 'get_used_times', ]
    list_filter = [IsUsedFilter, ]
    search_fields = ['text', ]

    def get_queryset(self, request):
        qs = super(KeywordAdmin, self).get_queryset(request)
        return (qs
                .prefetch_related('content_object')
                .annotate(used_times=models.Count('links')))

    def get_used_times(self, obj):
        return obj.used_times
    get_used_times.short_description = u'used times'


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['get_donor', 'get_recipient', 'get_keyword', ]
    list_filter = ['content_type', ]

    def get_queryset(self, request):
        qs = super(LinkAdmin, self).get_queryset(request)
        return (qs
                .select_related('keyword')
                .prefetch_related('donor', 'keyword__content_object'))

    def get_donor(self, obj):
        return obj.donor
    get_donor.short_description = _('From page')

    def get_recipient(self, obj):
        return obj.keyword.content_object
    get_recipient.short_description = _('To page')

    def get_keyword(self, obj):
        return obj.keyword.text
    get_keyword.short_description = _('Keyword')
