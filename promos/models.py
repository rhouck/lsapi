from django.db import models

from sales.models import Customer

import datetime


class Promo(models.Model):

    customer = models.ForeignKey(Customer)
    created_date = models.DateTimeField('date / time created')
    value = models.FloatField('promotion value')
    contract = models.OneToOneField('sales.Contract', blank=True, null=True) 
    code = models.CharField(max_length=16)

    def status(self):

    	if self.contract:
    		return "Closed"
    	else:
    		return "Open"


    def __unicode__(self):
		return "%s - %s - %s - %s" % (self.customer, self.code, self.value, self.status())

class Contest(models.Model):

	key = models.CharField(max_length=10, blank=True, null=True)
	created_date = models.DateTimeField('date / time created')
	expire_date = models.DateTimeField('date / time contest ends')
	origin_code = models.CharField(max_length=20)
	destination_code = models.CharField(max_length=20)
	decision_time = models.IntegerField(max_length=2)
	depart_date = models.DateField()
	return_date = models.DateField()
	value = models.FloatField('promotion value')
	closed = models.BooleanField('Closed and winnner notified', blank=True)
	end_price = models.FloatField(blank=True, null=True)

	def status(self):

		if self.closed:
			return "Closed"
		else:
			return "Open"

	def end_price_date(self):
		return self.created_date + datetime.timedelta(weeks=self.decision_time)

	def __unicode__(self):
		return "%s - %s / %s - %s" % (self.key, self.created_date.strftime('%b %d, %Y'), self.end_price_date().strftime('%b %d, %Y'), self.status())


class Submission(models.Model):

	contest = models.ForeignKey(Contest)
	customer = models.ForeignKey(Customer)
	created_date = models.DateTimeField('date / time created')
	value = models.FloatField('promotion value')

	def __unicode__(self):
		return "%s - %s" % (self.contest.key, self.customer)

    
