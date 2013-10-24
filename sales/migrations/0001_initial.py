# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Platform'
        db.create_table('sales_platform', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('org_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('web_site', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('contact_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('contact_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('reg_date', self.gf('django.db.models.fields.DateField')()),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
        ))
        db.send_create_signal('sales', ['Platform'])

        # Adding model 'Customer'
        db.create_table('sales_customer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('platform', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Platform'])),
            ('reg_date', self.gf('django.db.models.fields.DateField')()),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('address1', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True)),
            ('state_province', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('billing_address1', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('billing_city', self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True)),
            ('billing_state_province', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('billing_postal_code', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('billing_country', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('sales', ['Customer'])

        # Adding model 'Contract'
        db.create_table('sales_contract', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('customer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Customer'])),
            ('purch_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('search', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['pricing.Searches'], unique=True)),
            ('ex_fare', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ex_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('gateway_id', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('dep_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('ret_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('flight_choice', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('cc_last_four', self.gf('django.db.models.fields.IntegerField')(max_length=4, null=True, blank=True)),
            ('cc_exp_month', self.gf('django.db.models.fields.IntegerField')(max_length=2, null=True, blank=True)),
            ('cc_exp_year', self.gf('django.db.models.fields.IntegerField')(max_length=4, null=True, blank=True)),
        ))
        db.send_create_signal('sales', ['Contract'])

        # Adding model 'Staging'
        db.create_table('sales_staging', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contract', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.Contract'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('flight_choice', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('exercise', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('dep_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('ret_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('sales', ['Staging'])


    def backwards(self, orm):
        # Deleting model 'Platform'
        db.delete_table('sales_platform')

        # Deleting model 'Customer'
        db.delete_table('sales_customer')

        # Deleting model 'Contract'
        db.delete_table('sales_contract')

        # Deleting model 'Staging'
        db.delete_table('sales_staging')


    models = {
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
        },
        'sales.staging': {
            'Meta': {'object_name': 'Staging'},
            'contract': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sales.Contract']"}),
            'dep_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'exercise': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'flight_choice': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ret_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['sales']