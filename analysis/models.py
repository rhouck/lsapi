import math

from django.db import models
from django.db.models import Min
from sales.models import Contract
from api.views import current_time_aware, conv_to_js_date

"""
def calc_exposure_by_date(date=current_time_aware()):

    #@summary: this should be used to estimate risk expsore in extreme or 1% scenarios

    outstanding_options = Contract.objects.filter(search__exp_date__gte = date)
    exp_exposure = sum(opt.search.expected_risk for opt in outstanding_options if opt.outstanding())
    num_outstanding = sum(1 for opt in outstanding_options if opt.outstanding())
    if num_outstanding == 0:
        max_current_exposure = 0
    else:
        max_current_exposure = exp_exposure * 3
    js_date = conv_to_js_date(date)
    next_expiration = outstanding_options.aggregate(Min('search__exp_date'))['search__exp_date__min']

    return {'expected_exposure': exp_exposure, 'max_current_exposure': max_current_exposure, 'num_outstanding': num_outstanding, 'js_date': js_date, 'next_expiration': next_expiration}
"""

class Open(models.Model):
    status = models.BooleanField()

    def get_status(self):
        return bool(self.status)

    def __unicode__(self):

        if self.status:
            return "Open to new sales"
        else:
            return "Closed to new sales"
        #return str(self.status)



class Cash_reserve(models.Model):
    action_date = models.DateTimeField('date / time cash change')
    transaction = models.ForeignKey('sales.Contract', blank=True, null=True)
    cash_change = models.FloatField()
    cash_balance = models.FloatField()

    class Meta:
        verbose_name = "Cash Reserve"

    def __unicode__(self):
        return str(self.cash_balance)


class Additional_capacity(models.Model):

    quantity = models.IntegerField(max_length=6)

    class Meta:
        verbose_name = "Additional Capacity"


    def recalc_capacity(self, cash):
        # set's its own quantity value according to the rule defined below
        exposure = self.calc_exposure_by_date()
        excess_risk_per_opt = math.ceil((exposure['max_current_exposure']-exposure['expected_exposure'])/exposure['num_outstanding'])
        simple = math.floor((cash - exposure['max_current_exposure']) / excess_risk_per_opt) - 5
        rem_cap = max(simple, 0)
        self.quantity = rem_cap

        # if remaining capacity is zero, then automatically change the "open" status to False to prevent future sales
        if rem_cap == 0:
            update = Open.objects.get(pk=1)
            update.status = False
            update.save()

    """
    def recalc_capacity(self, cash):
        # set's its own quantity value according to the rule defined below
        exposure = calc_exposure_by_date()
        simple = math.floor((cash - exposure['max_current_exposure']) / 100.0) - 5
        rem_cap = max(simple, 0)
        self.quantity = rem_cap

        # if remaining capacity is zero, then automatically change the "open" status to False to prevent future sales
        if rem_cap == 0:
            update = Open.objects.get(pk=1)
            update.status = False
            update.save()
    """

    def calc_exposure_by_date(self, date=current_time_aware()):
        """
        @summary: this should be used to estimate risk expsore in extreme or 1% scenarios
        """
        # use multiple, not dollar amount here
        high_risk_grid = {
                            '5000': {10: 2.36, 50: 1.31, 100: 0.63, 250: 0.52, 50000: 0.26},
                            #'1000': {'10': 50, '50': 25, '100': 20, '200': 15, '500': 10},
                            #'5000': {'10': 70, '50': 50, '100': 40, '200': 25, '500': 20},
                        }


        outstanding_options = Contract.objects.filter(search__exp_date__gte = date)
        exp_exposure = sum(opt.search.expected_risk for opt in outstanding_options if opt.outstanding())
        num_outstanding = sum(1 for opt in outstanding_options if opt.outstanding())
        if num_outstanding == 0:
            max_current_exposure = 0
        else:
            bank = high_risk_grid['5000'].keys()
            bank.sort()
            for i in bank:
                if num_outstanding <= i:
                    max_current_exposure = exp_exposure * (high_risk_grid['5000'][i]+1)
                    break
        js_date = conv_to_js_date(date)
        next_expiration = outstanding_options.aggregate(Min('search__exp_date'))['search__exp_date__min']

        return {'expected_exposure': exp_exposure, 'max_current_exposure': max_current_exposure, 'num_outstanding': num_outstanding, 'js_date': js_date, 'next_expiration': next_expiration}


    def __unicode__(self):
        return str(self.quantity)


