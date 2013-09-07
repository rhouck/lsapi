from django.db import models

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

    # short search results
    locked_fare = models.FloatField(blank=True, null=True)
    holding_price = models.FloatField(blank=True, null=True)
    error = models.CharField(max_length=200, blank=True, null=True)

    # returned from search results
    """
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
    """

    class Meta:
        verbose_name = "Search History"

    def get_status(self):
        return bool(self.open_status)

    def __unicode__(self):
        return "%s - %s:%s" % (self.search_date, self.origin_code, self.destination_code)
