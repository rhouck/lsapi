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
    key = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return self.org_name


class Customer(models.Model):
    key = models.CharField(max_length=10)
    email = models.EmailField(max_length=75)
    #password = models.CharField(max_length=200)
    platform = models.ForeignKey(Platform)
    reg_date = models.DateField('date registered')
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=60, blank=True, null=True)
    state_prov = models.CharField('state / province', max_length=30, blank=True, null=True)
    zip_code = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)


    def __unicode__(self):
        if self.first_name and self.last_name:
            tag = "%s %s" % (self.first_name, self.last_name)
        else:
            tag = self.email
        return tag


class Contract(models.Model):
    #platform = models.ForeignKey(Platform)
    customer = models.ForeignKey(Customer)
    purch_date = models.DateTimeField('date / time purchased')
    search = models.OneToOneField('pricing.Search_history') # , primary_key=True
    ex_fare = models.FloatField('exercised fare', blank=True, null=True)
    ex_date = models.DateTimeField('date / time exercised', blank=True, null=True)

    def outstanding(self):
        return self.search.exp_date >= current_time_aware().date() and not self.ex_date

    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Still open and valid?'

    def __unicode__(self):
        #uni_name = '%s - %s - %s' % (self.purch_date, self.customer.platform, self.customer)
        uni_name = '%s - %s' % (self.purch_date, self.customer)
        return uni_name


class Open(models.Model):
    status = models.BooleanField()

    def get_status(self):
        return bool(self.status)

    def __unicode__(self):
        return str(self.status)
