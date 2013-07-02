from api.views import current_time_aware
import datetime
from django.utils import timezone

from django.db import models


class Platform(models.Model):
    org_name = models.CharField(max_length=200)
    web_site = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField(max_length=75)
    reg_date = models.DateField('date registered')
    key = models.CharField(max_length=10)

    def __unicode__(self):
        return self.org_name


class Customer(models.Model):
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(max_length=75)
    #password = models.CharField(max_length=200)
    reg_date = models.DateField('date registered')
    key = models.CharField(max_length=10)

    def __unicode__(self):
        if self.first_name and self.last_name:
            tag = "%s %s" % (self.first_name, self.last_name)
        else:
            tag = self.email
        return tag


class Contract(models.Model):
    platform = models.ForeignKey(Platform)
    customer = models.ForeignKey(Customer)
    purch_date = models.DateTimeField('date / time purchased')
    search = models.OneToOneField('analysis.Search_history', primary_key=True)
    ex_fare = models.FloatField('exercised fare', blank=True, null=True)
    ex_date = models.DateTimeField('date / time exercised', blank=True, null=True)


    def outstanding(self):
        return self.search.exp_date >= current_time_aware().date() and not self.ex_fare
    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Still open and valid?'

    def __unicode__(self):
        uni_name = '%s - %s - %s' % (self.purch_date, self.platform, self.customer)
        return uni_name


class Open(models.Model):
    status = models.BooleanField()

    def get_status(self):
        return bool(self.status)

    def __unicode__(self):
        return str(self.status)
