from django import forms


class Exercise_option(forms.Form):
    cust_email = forms.EmailField()
    cust_password = forms.CharField(widget=forms.PasswordInput())
    org_name = forms.CharField(label='Platform')
    search_key = forms.CharField(label='Key')
    exercise_fare = forms.FloatField()


class Customer_login(forms.Form):
    email = forms.EmailField()
    #password = forms.CharField(widget=forms.PasswordInput())


class Customer_signup(Customer_login):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)


class Purchase_option(Customer_signup):
    org_name = forms.CharField(label='Platform')
    search_key = forms.CharField(label='Key')
