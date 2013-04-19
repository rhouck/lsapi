from django import forms

from sales.models import Open


class Projection(forms.Form):
    origin = forms.CharField(label='From', initial="SFO")
    destination = forms.CharField(label='To')
    num_high_days = forms.IntegerField(label='Weekday category', initial=1)
    depart_times = forms.IntegerField(label='Depart pref', initial=0)
    return_times = forms.IntegerField(label='Return pref', initial=0)
    nonstop = forms.IntegerField(label='Nonstop pref', initial=0)
         

class Overlay(Projection):
    proj_date = forms.DateField(label='Projection Date')
    num_per_look_back = forms.IntegerField(label='Lookback Dist', initial=10)
    weight_on_imp = forms.FloatField(label='Implied/Historical', initial=1)
    ensure_suf_data = forms.FloatField(label='Suf Data Req', initial=.8)
    seasonality_adjust = forms.BooleanField(label='Seasonality', required=False, initial=True)
    regressed = forms.BooleanField(label='Regress to mean', required=False, initial=False)
    

class Historical(Projection):
    trip_length_min = forms.IntegerField(label='Min trip Length', initial=6)
    trip_length_max = forms.IntegerField(label='Max trip Length', initial=15)
    depart_length_max = forms.IntegerField(label='Max weeks before departure', initial=10)
    num_high_days = forms.IntegerField(label='Weekday category', required=False)
    

class Simulation(forms.Form):
    source = forms.CharField(label='Table name', required=False)
    route = forms.CharField(label='Single route', required=False)

 
 
class Dashboard_current(forms.Form):
    #open = forms.BooleanField(label='Enable sale of options', required=False, initial=Open.objects.get(pk=1).get_status()) 
    #force_stop = forms.BooleanField(label='Force stop option sales', required=False, initial=False)
    cash_change = forms.FloatField(label='Change in cash balance', required=False)
    change_status = forms.BooleanField(label='Flip open sales status', required=False, initial=False)