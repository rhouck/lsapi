import math

from django.db import models
from django.db.models import Min
from sales.models import Open, Contract
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

class Search_history(models.Model):
    search_date = models.DateTimeField('date / time searched')
    exp_date = models.DateField('expiration date', blank=True, null=True)
    open_status = models.BooleanField('available capacity')
    key = models.CharField(max_length=10, blank=True, null=True)
    # from search inputs
    origin_code = models.CharField(max_length=20)
    destination_code = models.CharField(max_length=20)
    holding_per = models.IntegerField(max_length=5)
    depart_date1 = models.DateField('first depart date')
    depart_date2 = models.DateField('second depart date')
    return_date1 = models.DateField('first return date', blank=True, null=True)
    return_date2 = models.DateField('second return date', blank=True, null=True)
    search_type = models.CharField('round trip / one way', max_length=200)
    depart_times = models.IntegerField('departure time preference', max_length=5)
    return_times = models.IntegerField('return time preference', max_length=5)
    nonstop = models.IntegerField('non-stop flight preference', max_length=5)
    # returned from search results
    buffer = models.FloatField(blank=True, null=True)
    correl_coef = models.FloatField(blank=True, null=True)
    cycles = models.IntegerField(max_length=10, blank=True, null=True)
    expected_risk = models.FloatField(blank=True, null=True)
    lockin_per = models.IntegerField(max_length=3, blank=True, null=True)
    markup = models.FloatField(blank=True, null=True)
    round_to = models.FloatField(blank=True, null=True)
    wtp = models.FloatField('willingness to pay (% locked fare)', blank=True, null=True)
    wtpx = models.FloatField('willingness to pay ($ per weekd/day interval)', blank=True, null=True)
    max_trip_length = models.IntegerField('max trip length (weeks)', max_length=3, blank=True, null=True)
    locked_fare = models.FloatField(blank=True, null=True)
    holding_price = models.FloatField(blank=True, null=True)
    error = models.CharField(max_length=200, blank=True, null=True)
    geography = models.CharField(max_length=10)
    # calculated from search results
    first_week_avg_proj_fare = models.FloatField('1st wk avg fare', blank=True, null=True)
    first_week_max_proj_fare = models.FloatField('1st wk max fare', blank=True, null=True)
    second_week_avg_proj_fare = models.FloatField('2nd wk avg fare', blank=True, null=True)
    second_week_max_proj_fare = models.FloatField('2nd wk max fare', blank=True, null=True)
    first_week_avg_proj_st_dev = models.FloatField('1st wk avg stdev', blank=True, null=True)
    first_week_max_proj_st_dev = models.FloatField('1st wk max stdev', blank=True, null=True)
    second_week_avg_proj_st_dev = models.FloatField('2nd wk avg stdev', blank=True, null=True)
    second_week_max_proj_st_dev = models.FloatField('2nd wk max stdev', blank=True, null=True)
    total_flexibility = models.IntegerField(max_length=3)
    time_to_departure = models.IntegerField(max_length=3)


    class Meta:
        verbose_name = "Search History"

    def get_status(self):
        return bool(self.open_status)

    def __unicode__(self):
        return "%s - %s:%s" % (self.search_date, self.origin_code, self.destination_code)



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
        simple = math.floor((cash - exposure['max_current_exposure']) / 100.0) - 5
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


    def __unicode__(self):
        return str(self.quantity)
