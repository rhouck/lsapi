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
    address1 = forms.CharField(required=False)
    city = forms.CharField(required=False)
    state_province = forms.CharField(required=False)
    postal_code = forms.CharField(required=False)
    country = forms.CharField(required=False)


class PaymentForm(Customer_signup):
    #first_name = forms.CharField(max_length=50)
    #last_name = forms.CharField(max_length=50)
    number = forms.CharField(max_length=16, label="card number")
    month = forms.CharField(max_length=2, label="expiration month")
    year = forms.CharField(max_length=4, label="expiration year")
    code = forms.CharField(max_length=4, label="security code")

class Purchase_option(forms.Form):
    search_key = forms.CharField(label='Search Key')
    cust_key = forms.CharField(label='Customer Key')
    number = forms.CharField(max_length=16, label="card number")
    month = forms.CharField(max_length=2, label="expiration month")
    year = forms.CharField(max_length=4, label="expiration year")
    code = forms.CharField(max_length=4, label="security code")