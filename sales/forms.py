from django import forms

class Purchase_option(forms.Form):
    cust_email = forms.EmailField()
    cust_password = forms.CharField(widget=forms.PasswordInput())
    org_name = forms.CharField(label='Platform')
    search_id = forms.IntegerField(label='Id')


class Exercise_option(forms.Form):
    cust_email = forms.EmailField()
    cust_password = forms.CharField(widget=forms.PasswordInput())
    org_name = forms.CharField(label='Platform')
    search_id = forms.IntegerField(label='Id')
    exercise_fare = forms.FloatField()


class Customer_signup(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

