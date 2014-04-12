from django.db import models

from sales.models import Customer


class Promo(models.Model):

    customer = models.ForeignKey(Customer)
    created_date = models.DateTimeField('date / time created')
    value = models.FloatField('promotion value')
    contract = models.OneToOneField('sales.Contract', blank=True, null=True) 
    code = models.CharField(max_length=16)


class Contest(models.Model):

    created_date = models.DateTimeField('date / time created')
    expire_date = models.DateTimeField('date / time contest ends')
    origin_code = models.CharField(max_length=20)
    destination_code = models.CharField(max_length=20)
    depart_date = models.DateField()
    return_date = models.DateField()
    value = models.FloatField('promotion value')

    