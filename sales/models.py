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
    platform = models.ForeignKey(Platform)
    reg_date = models.DateField('date registered')
    email = models.EmailField(max_length=75)
    phone = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)


    def __unicode__(self):
        if self.first_name and self.last_name:
            tag = "%s %s" % (self.first_name, self.last_name)
        else:
            tag = self.email
        return tag



class Contract(models.Model):
    customer = models.ForeignKey(Customer)
    purch_date = models.DateTimeField('date / time purchased')
    search = models.OneToOneField('pricing.Searches') # , primary_key=True
    ex_fare = models.FloatField('exercised fare', blank=True, null=True)
    ex_date = models.DateTimeField('date / time exercised', blank=True, null=True)
    gateway_id = models.CharField(max_length=20, blank=True, null=True)
    dep_date = models.DateField('depart date', blank=True, null=True)
    ret_date = models.DateField('return date', blank=True, null=True)
    close_staged_date = models.DateTimeField('date / time closed staging', blank=True, null=True)

    flight_choice = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    flight_purchased = models.TextField(blank=True, null=True)

    # traveler information
    traveler_first_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_middle_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_last_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_infant = models.BooleanField('travel w/ infant', blank=True)
    traveler_gender = models.CharField(max_length=20, blank=True, null=True)
    traveler_birth_date = models.DateField(blank=True, null=True)
    traveler_passport_country = models.CharField(max_length=20, blank=True, null=True)
    traveler_seat_pref = models.CharField(max_length=20, blank=True, null=True)
    traveler_rewards_program = models.CharField(max_length=100, blank=True, null=True)
    traveler_contact_email = models.EmailField(max_length=75, blank=True, null=True)

    # billing information
    billing_first_name = models.CharField(max_length=200, blank=True, null=True)
    billing_middle_name = models.CharField(max_length=200, blank=True, null=True)
    billing_last_name = models.CharField(max_length=200, blank=True, null=True)
    billing_phone = models.CharField(max_length=20, blank=True, null=True)
    billing_address1 = models.CharField(max_length=50, blank=True, null=True)
    billing_address2 = models.CharField(max_length=50, blank=True, null=True)
    billing_city = models.CharField(max_length=60, blank=True, null=True)
    billing_province = models.CharField('billing state / province', max_length=30, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=50, blank=True, null=True)
    billing_country = models.CharField(max_length=50, blank=True, null=True)

    cc_last_four = models.IntegerField(max_length=4, blank=True, null=True)
    cc_exp_month = models.IntegerField(max_length=2, blank=True, null=True)
    cc_exp_year = models.IntegerField(max_length=4, blank=True, null=True)


    def outstanding(self):
        return self.search.exp_date >= current_time_aware().date() and not self.ex_date
    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Open and not expired'

    def expired(self):
        return self.search.exp_date < current_time_aware().date()

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

    traveler_first_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_middle_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_last_name = models.CharField(max_length=200, blank=True, null=True)
    traveler_infant = models.BooleanField('travel w/ infant', blank=True)
    traveler_gender = models.CharField(max_length=20, blank=True, null=True)
    traveler_birth_date = models.DateField(blank=True, null=True)
    traveler_passport_country = models.CharField(max_length=20, blank=True, null=True)
    traveler_seat_pref = models.CharField(max_length=20, blank=True, null=True)
    traveler_rewards_program = models.CharField(max_length=100, blank=True, null=True)
    traveler_contact_email = models.EmailField(max_length=75, blank=True, null=True)

    def __unicode__(self):
        uni_name = '%s' % (self.contract)
        return uni_name
