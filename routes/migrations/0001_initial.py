# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Routes'
        db.create_table('routes_routes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('org_code', self.gf('django.db.models.fields.TextField')()),
            ('dest_code', self.gf('django.db.models.fields.TextField')()),
            ('org_full', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('dest_full', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('routes', ['Routes'])


    def backwards(self, orm):
        # Deleting model 'Routes'
        db.delete_table('routes_routes')


    models = {
        'routes.routes': {
            'Meta': {'object_name': 'Routes'},
            'dest_code': ('django.db.models.fields.TextField', [], {}),
            'dest_full': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org_code': ('django.db.models.fields.TextField', [], {}),
            'org_full': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['routes']