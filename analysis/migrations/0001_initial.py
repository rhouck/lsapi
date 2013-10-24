# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Open'
        db.create_table('analysis_open', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('analysis', ['Open'])

        # Adding model 'Cash_reserve'
        db.create_table('analysis_cash_reserve', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('transaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Contract'], null=True, blank=True)),
            ('cash_change', self.gf('django.db.models.fields.FloatField')()),
            ('cash_balance', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('analysis', ['Cash_reserve'])

        # Adding model 'Additional_capacity'
        db.create_table('analysis_additional_capacity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(max_length=6)),
        ))
        db.send_create_signal('analysis', ['Additional_capacity'])


    def backwards(self, orm):
        # Deleting model 'Open'
        db.delete_table('analysis_open')

        # Deleting model 'Cash_reserve'
        db.delete_table('analysis_cash_reserve')

        # Deleting model 'Additional_capacity'
        db.delete_table('analysis_additional_capacity')


    models = {
        'analysis.additional_capacity': {
            'Meta': {'object_name': 'Additional_capacity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'max_length': '6'})
        },
        'analysis.cash_reserve': {
            'Meta': {'object_name': 'Cash_reserve'},
            'action_date': ('django.db.models.fields.DateTimeField', [], {}),
            'cash_balance': ('django.db.models.fields.FloatField', [], {}),
            'cash_change': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'transaction': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.Contract']", 'null': 'True', 'blank': 'True'})
        },
        'analysis.open': {
            'Meta': {'object_name': 'Open'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'pricing.searches': {
            'Meta': {'object_name': 'Searches'},
            'convenience': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
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
        },
        'sales.contract': {
            'Meta': {'object_name': 'Contract'},
            'cc_exp_month': ('django.db.models.fields.IntegerField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'cc_exp_year': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'cc_last_four': ('django.db.models.fields.IntegerField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.Customer']"}),
            'dep_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'ex_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ex_fare': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'flight_choice': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gateway_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'purch_date': ('django.db.models.fields.DateTimeField', [], {}),
            'ret_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'search': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['pricing.Searches']", 'unique': 'True'})
        },
        'sales.customer': {
            'Meta': {'object_name': 'Customer'},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'billing_address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'billing_city': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'billing_country': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'billing_postal_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'billing_state_province': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'platform': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.Platform']"}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'reg_date': ('django.db.models.fields.DateField', [], {}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'sales.platform': {
            'Meta': {'object_name': 'Platform'},
            'contact_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'org_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'reg_date': ('django.db.models.fields.DateField', [], {}),
            'web_site': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['analysis']