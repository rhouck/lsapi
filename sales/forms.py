from django import forms


class Exercise_option(forms.Form):
    cust_key = forms.CharField()
    search_key = forms.CharField()
    exercise = forms.BooleanField(required=False)


class Customer_login(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    platform_key = forms.CharField(label='Platform Key')

class Customer_signup(Customer_login):
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone = forms.CharField()
    address = forms.CharField()
    city = forms.CharField()
    state_prov = forms.CharField()
    zip_code = forms.CharField()
    country = forms.CharField()

class Purchase_option(forms.Form):
    #platform_key = forms.CharField(label='Platform Key')
    search_key = forms.CharField(label='Search Key')
    cust_key = forms.CharField(label='Customer Key')
