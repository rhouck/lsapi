from django import forms


class Exercise_option(forms.Form):
    cust_key = forms.CharField()
    search_key = forms.CharField()
    exercise = forms.BooleanField(required=False)


class Customer_login(forms.Form):
    email = forms.EmailField()
    #password = forms.CharField(widget=forms.PasswordInput())
    platform_key = forms.CharField(label='Platform Key')

class Customer_signup(Customer_login):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    address = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state_prov = forms.CharField(required=False)
    zip_code = forms.CharField(required=False)
    country = forms.CharField(required=False)

class Purchase_option(forms.Form):
    #platform_key = forms.CharField(label='Platform Key')
    search_key = forms.CharField(label='Search Key')
    cust_key = forms.CharField(label='Customer Key')
