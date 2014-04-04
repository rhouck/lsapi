from django import forms

from models import Open


class Projection(forms.Form):
    origin = forms.CharField(label='From', initial="SFO")
    destination = forms.CharField(label='To')
    num_high_days = forms.IntegerField(label='Wkdy cat', initial=1)
    depart_times = forms.IntegerField(label='Dpt pref', initial=0)
    return_times = forms.IntegerField(label='Ret pref', initial=0)
    nonstop = forms.IntegerField(label='Stop pref', initial=0)


class Overlay(Projection):
    proj_date = forms.DateField(label='Proj Date')
    num_per_look_back = forms.IntegerField(label='Lkbk Dist', initial=10)
    weight_on_imp = forms.FloatField(label='Imp/Hist', initial=1)
    ensure_suf_data = forms.FloatField(label='Suf Data Req', initial=.8)
    black_list_error = forms.FloatField(label='Blck Lst Err', required=False, initial=None)
    depart_length_width = forms.IntegerField(label='Dep Len Wid', initial=1)
    width_of_avg = forms.IntegerField(label='Wid Avg', initial=1)
    num_wks_proj_out = forms.IntegerField(label='Proj Dist', initial=20)
    final_proj_week = forms.IntegerField(label='Final Proj Wk', initial=1)
    first_proj_week = forms.IntegerField(label='First Proj Wk', initial=20)
    seasonality_adjust = forms.BooleanField(label='Seas.', required=False, initial=True)
    regressed = forms.BooleanField(label='Regress', required=False, initial=False)


class Historical(Projection):
    trip_length_min = forms.IntegerField(label='Min trip Len', initial=6)
    trip_length_max = forms.IntegerField(label='Max trip Len', initial=15)
    depart_length_max = forms.IntegerField(label='Max wks b4 dep', initial=10)
    num_high_days = forms.IntegerField(label='Wkdy cat', required=False)


class Simulation(forms.Form):
    source = forms.CharField(label='Table name', required=False)
    route = forms.CharField(label='Single route', required=False)



class Dashboard_current(forms.Form):
    #open = forms.BooleanField(label='Enable sale of options', required=False, initial=Open.objects.get(pk=1).get_status())
    #force_stop = forms.BooleanField(label='Force stop option sales', required=False, initial=False)
    cash_change = forms.FloatField(label='Change in cash balance', required=False)
    #change_status = forms.BooleanField(label='Open Status', required=False, initial=False)



class PerformanceForm(forms.Form):
    beg_date = forms.DateField(label='Beginning Date')
    end_date = forms.DateField(label='Ending Date')