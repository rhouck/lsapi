from django.db import models

from sales.models import Customer

# Create your models here.
class Promo(models.Model):

    customer = models.ForeignKey(Customer)
    created_date = models.DateTimeField('date / time created')
    value = models.FloatField('promotion value')
    contract = models.OneToOneField('sales.Contract', blank=True, null=True) 
    code = models.CharField(max_length=16)