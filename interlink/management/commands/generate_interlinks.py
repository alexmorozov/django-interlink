#--coding: utf8--

from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _

from interlink.tasks import generate_interlinks


class Command(BaseCommand):
    help = _('Generates the SEO interlinks between objects')

    def handle(self, *args, **options):
        total_links, created, skipped = generate_interlinks()
        self.stdout.write(
            '%d links created for %d objects, %d objects had no candidates' % (
                total_links, created, skipped
            ))
