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
    address1 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=60, blank=True, null=True)
    state_province = models.CharField('state / province', max_length=30, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    # billing information
    billing_address1 = models.CharField(max_length=50, blank=True, null=True)
    billing_city = models.CharField(max_length=60, blank=True, null=True)
    billing_state_province = models.CharField('state / province', max_length=30, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=50, blank=True, null=True)
    billing_country = models.CharField(max_length=50, blank=True, null=True)


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
    search = models.OneToOneField('pricing.Searches') # , primary_key=True
    ex_fare = models.FloatField('exercised fare', blank=True, null=True)
    ex_date = models.DateTimeField('date / time exercised', blank=True, null=True)
    gateway_id = models.CharField(max_length=20, blank=True, null=True)
    dep_date = models.DateField('depart date', blank=True, null=True)
    ret_date = models.DateField('return date', blank=True, null=True)
    flight_choice = models.TextField(blank=True, null=True)
    # non-sensitive credit card info
    cc_last_four = models.IntegerField(max_length=4, blank=True, null=True)
    cc_exp_month = models.IntegerField(max_length=2, blank=True, null=True)
    cc_exp_year = models.IntegerField(max_length=4, blank=True, null=True)

    def outstanding(self):
        return self.search.exp_date >= current_time_aware().date() and not self.ex_date
    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Open and not expired'


    def staged(self):
        try:
            find_staged = Staging.objects.get(contract=self.id)
            val = True
        except:
            val = False
        return val
    staged.boolean = True
    staged.short_description = 'In staging'


    def __unicode__(self):
        uni_name = '%s - %s - %s' % (self.customer, self.customer.platform, self.purch_date.strftime('%b %d, %Y'))
        return uni_name


class Staging(models.Model):
    contract = models.ForeignKey(Contract)
    notes = models.TextField(blank=True, null=True)
    flight_choice = models.TextField(blank=True, null=True)
    exercise = models.BooleanField(blank=True)
    dep_date = models.DateField('depart date', blank=True, null=True)
    ret_date = models.DateField('return date', blank=True, null=True)

    def __unicode__(self):
        uni_name = '%s' % (self.contract)
        return uni_name
