# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interlink', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='keyword',
            old_name='keyword',
            new_name='text',
        ),
    ]
