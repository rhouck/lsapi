from django import forms


class Exercise_option(forms.Form):
    cust_email = forms.EmailField()
    cust_password = forms.CharField(widget=forms.PasswordInput())
    org_name = forms.CharField(label='Platform')
    search_key = forms.CharField(label='Key')
    exercise_fare = forms.FloatField()


class Customer_login(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


class Customer_signup(Customer_login):
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone = forms.CharField()
    address = forms.CharField()
    city= forms.CharField()
    state_prov = forms.CharField()
    zip_code = forms.CharField()
    country = forms.CharField()

class Purchase_option(forms.Form):
    platform_key = forms.CharField(label='Platform Key')
    search_key = forms.CharField(label='Search Key')
    cust_key = forms.CharField(label='Customer Key')
