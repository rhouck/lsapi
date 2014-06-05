from api.views import current_time_aware
from api.settings import HIGHRISE_CONFIG, MODE

import datetime
from django.utils import timezone

from django.db import models

import pyrise


class Platform(models.Model):
    org_name = models.CharField(max_length=200)
    web_site = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField(max_length=75)
    reg_date = models.DateField('date registered')
    key = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return self.org_name
        #return "%s - %s" % (self.org_name, self.web_site)


class Customer(models.Model):
    
    key = models.CharField(max_length=10)
    platform = models.ForeignKey(Platform)
    reg_date = models.DateField('date registered')
    email = models.EmailField(max_length=75)
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    
    billdotcom_id = models.CharField(max_length=50, blank=True, null=True)
    highrise_id = models.CharField(max_length=50, blank=True, null=True)


    def count_outstanding_contracts(self):
        
        contracts = Contract.objects.filter(customer=self)

        count = 0
        for i in contracts:
            if i.outstanding():
                count += 1
        return count

    def create_highrise_account(self):

        if not self.highrise_id: # and MODE == 'live':
            try:
                pyrise.Highrise.set_server(HIGHRISE_CONFIG['server'])
                pyrise.Highrise.auth(HIGHRISE_CONFIG['auth'])
                cust = pyrise.Person()
                   
                cust.contact_data = pyrise.ContactData(email_addresses=[pyrise.EmailAddress(address=self.email, location='Home'),],)
                
                cust.first_name = self.first_name if self.first_name else self.email
                
                if self.last_name:
                    cust.last_name = self.last_name
                if self.phone:
                    cust.contact_data.phone_numbers = [pyrise.PhoneNumber(number=self.phone, location='Home'),]

                
                cust.save()
                cust.add_tag('user')
                cust.add_tag(str(self.platform))

                self.highrise_id = cust.id
                self.save()
            except:
                pass

    def add_highrise_tag(self, tag):

        if self.highrise_id:
            try:
                pyrise.Highrise.set_server(HIGHRISE_CONFIG['server'])
                pyrise.Highrise.auth(HIGHRISE_CONFIG['auth'])
                cust = pyrise.Person.get(self.highrise_id)
                cust.add_tag(tag)
            except:
                pass


    def update_highrise(self, inputs):
        
        if self.highrise_id:
            pyrise.Highrise.set_server(HIGHRISE_CONFIG['server'])
            pyrise.Highrise.auth(HIGHRISE_CONFIG['auth'])
            
            cust = pyrise.Person.get(self.highrise_id)

            if "email" in inputs:
                exists = False
                for i in cust.contact_data.email_addresses:
                    if i.address == inputs['email']:
                        exists = True
                if not exists:
                    cust.contact_data.email_addresses.append(pyrise.EmailAddress(address=inputs['email'], location='Home'))
            
            if "phone" in inputs:
                exists = False
                for i in cust.contact_data.phone_numbers:
                    if i.number == inputs['phone']:
                        exists = True
                if not exists:
                    cust.contact_data.phone_numbers.append(pyrise.PhoneNumber(number=inputs['phone'], location='Home'))
            
            if 'first_name' in inputs:
                cust.first_name = inputs['first_name']
            if 'last_name' in inputs:
                cust.last_name = inputs['last_name']

            cust.save()


    def __unicode__(self):
        
        tag = ""
        if self.first_name and self.last_name:
            tag += "%s %s - " % (self.first_name, self.last_name)
        tag += self.email
        tag += " - %s" % (self.platform)
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

    refunded = models.BooleanField('fully refunded transaction', blank=True)

    """
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
    """

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

    # shipping address
    shipping_address1 = models.CharField(max_length=50, blank=True, null=True)
    shipping_address2 = models.CharField(max_length=50, blank=True, null=True)
    shipping_city = models.CharField(max_length=60, blank=True, null=True)
    shipping_province = models.CharField('billing state / province', max_length=30, blank=True, null=True)
    shipping_postal_code = models.CharField(max_length=50, blank=True, null=True)
    shipping_country = models.CharField(max_length=50, blank=True, null=True)

    alerts = models.BooleanField('receive alerts', blank=True)

    def outstanding(self):
        current_time = current_time_aware()
        current_date = datetime.datetime(current_time.year, current_time.month, current_time.day,0,0)
        exp_date = datetime.datetime(self.search.exp_date.year, self.search.exp_date.month, self.search.exp_date.day,0,0)
        return exp_date >= (current_date - datetime.timedelta(days=1)) and not self.ex_date
    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Open and not expired'

    def expired(self):
        current_time = current_time_aware()
        current_date = datetime.datetime(current_time.year, current_time.month, current_time.day,0,0)
        exp_date = datetime.datetime(self.search.exp_date.year, self.search.exp_date.month, self.search.exp_date.day,0,0)
        return exp_date < (current_date - datetime.timedelta(days=1))

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
        uni_name = '%s - %s - %s' % (self.search, self.customer, self.search.exp_date.strftime('%b %d, %Y'))
        #uni_name = '%s - %s - %s' % (self.customer, self.customer.platform, self.purch_date.strftime('%b %d, %Y'))
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


class Demo(models.Model):
    customer = models.ForeignKey(Customer)
    purch_date = models.DateTimeField('date / time purchased')
    search = models.OneToOneField('pricing.Searches') # , primary_key=True

    alerts = models.BooleanField('receive alerts', blank=True)

    def outstanding(self):
        return self.search.exp_date >= current_time_aware()
    outstanding.admin_order_field = 'search__exp_date'
    outstanding.boolean = True
    outstanding.short_description = 'Open and not expired'

    def expired(self):
        return self.search.exp_date < current_time_aware()

    def __unicode__(self):
        uni_name = '%s - %s - %s' % (self.customer, self.customer.platform, self.purch_date.strftime('%b %d, %Y'))
        return uni_name

class AlertsCheck(models.Model):
    run_date = models.DateTimeField('date / time run')

class Alerts(models.Model):
    search = models.OneToOneField('pricing.Searches')
    fares = models.TextField(blank=True, null=True)
    update_date = models.DateTimeField('date last updated', null=True)


