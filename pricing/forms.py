from django import forms

class gen_price_multiple(forms.Form):
    origin_code = forms.CharField(required=False)
    destination_code = forms.CharField(required=False)
    holding_per = forms.IntegerField()
    #lockin_per = forms.IntegerField(required=False)
    depart_date1 = forms.DateField()
    return_date1 = forms.DateField()
    #search_type = forms.CharField()
    depart_times = forms.IntegerField()
    return_times = forms.IntegerField()
    nonstop = forms.IntegerField()

class gen_price_single(gen_price_multiple):
    depart_date2 = forms.DateField()
    return_date2 = forms.DateField()


class search_summary_inputs(forms.Form):
    origin_code = forms.CharField()
    destination_code = forms.CharField()
    search_type = forms.CharField()
    depart_times = forms.IntegerField()
    return_times = forms.IntegerField()
    nonstop = forms.IntegerField()

class full_option_info(forms.Form):
    origin_code = forms.CharField(required=False)
    destination_code = forms.CharField(required=False)
    holding_per = forms.IntegerField()
    depart_date1 = forms.DateField()
    depart_date2 = forms.DateField()
    return_date1 = forms.DateField()
    return_date2 = forms.DateField()
    depart_times = forms.CharField()
    return_times = forms.CharField()
    convenience = forms.CharField()
    # select flight search results display
    #show_flights = forms.BooleanField(required=False, initial=True)
    disp_depart_date = forms.DateField(required=False)
    disp_return_date = forms.DateField(required=False)


class flights_display(forms.Form):
    depart_date = forms.DateField()
    return_date = forms.DateField()
