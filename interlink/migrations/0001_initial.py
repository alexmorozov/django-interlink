# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField(db_index=True)),
                ('keyword', models.CharField(help_text='Django templating supported with {{ object }} being the current object', max_length=100)),
                ('weight', models.IntegerField(default=1, help_text='Repeat keyword several times', choices=[(1, 1), (2, 2), (3, 3)])),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField(db_index=True)),
                ('order', models.IntegerField(default=0)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('keyword', models.ForeignKey(to='interlink.Keyword')),
            ],
        ),
    ]
