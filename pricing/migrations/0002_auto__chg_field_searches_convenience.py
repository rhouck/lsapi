# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Searches.convenience'
        db.alter_column('pricing_searches', 'convenience', self.gf('django.db.models.fields.CharField')(max_length=5))

    def backwards(self, orm):

        # Changing field 'Searches.convenience'
        db.alter_column('pricing_searches', 'convenience', self.gf('django.db.models.fields.CharField')(max_length=25))

    models = {
        'pricing.searches': {
            'Meta': {'object_name': 'Searches'},
            'convenience': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'depart_date1': ('django.db.models.fields.DateField', [], {}),
            'depart_date2': ('django.db.models.fields.DateField', [], {}),
            'depart_times': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'destination_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'exp_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'expected_risk': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'holding_per': ('django.db.models.fields.IntegerField', [], {'max_length': '5'}),
            'holding_price': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'locked_fare': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'open_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'origin_code': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'return_date1': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'return_date2': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'return_times': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'search_date': ('django.db.models.fields.DateTimeField', [], {}),
            'search_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'time_to_departure': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'total_flexibility': ('django.db.models.fields.IntegerField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricing']