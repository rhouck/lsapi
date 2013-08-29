from django import forms

class FareChanges(forms.Form):
    route = forms.CharField(label='Route')
    min_dep_len = forms.IntegerField(label='Min Depart Length', initial=30, required=False)
    max_dep_len = forms.IntegerField(label='Max Depart Length', initial=40, required=False)
    proj_int = forms.IntegerField(label='Projection Interval', initial=7)
    min_date_comp = forms.DateField(label='Earliest Date Completed', required=False)
    max_date_comp = forms.DateField(label='Latest Date Completed', required=False)
    dep_wkday = forms.IntegerField(label='Departing Weekday', required=False)
    ret_wkday = forms.IntegerField(label='Returning Weekday', required=False)


