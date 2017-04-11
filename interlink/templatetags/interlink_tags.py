# --coding: utf8--

from django import template
from django.template.defaultfilters import slice_filter
from django.template.loader import select_template, render_to_string

from interlink.models import Link

register = template.Library()


@register.assignment_tag
def interlinks_for(item, slice=None):
    links = Link.objects.outgoing(item)
    if slice:
        links = slice_filter(links, slice)
    rendered_links = []
    for link in links:
        page = link.keyword.content_object
        if page:
            tpl = select_template([
                'interlink/%s/link.html' % page._meta.app_label,
                'interlink/%s/%s_link.html' % (page._meta.app_label,
                                               page._meta.model_name),
                'interlink/link.html',
            ])
            context = template.Context(dict(link=link))
            rendered_links.append(tpl.render(context))
    if not rendered_links:
        return ''
    return render_to_string('interlink/links_list.html',
                            dict(links=rendered_links))
