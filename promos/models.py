from django.db import models

from sales.models import Customer


class Promo(models.Model):

    customer = models.ForeignKey(Customer)
    created_date = models.DateTimeField('date / time created')
    value = models.FloatField('promotion value')
    contract = models.OneToOneField('sales.Contract', blank=True, null=True) 
    code = models.CharField(max_length=16)


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


class Submission(models.Model):

	contest = models.ForeignKey(Contest)
	customer = models.ForeignKey(Customer)
	created_date = models.DateTimeField('date / time created')
	value = models.FloatField('promotion value')

    
