from django import forms



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
    state_province = forms.CharField(label="state / province", required=False)
    postal_code = forms.CharField(required=False)
    country = forms.CharField(required=False)
    # billing information
    billing_address1 = forms.CharField(required=False)
    billing_city = forms.CharField(required=False)
    billing_province = forms.CharField(label="state / province", required=False)
    billing_postal_code = forms.CharField(required=False)
    billing_country = forms.CharField(required=False)

class PaymentForm(Customer_signup):
    #first_name = forms.CharField(max_length=50)
    #last_name = forms.CharField(max_length=50)
    number = forms.CharField(max_length=16, label="card number")
    month = forms.CharField(max_length=2, label="expiration month")
    year = forms.CharField(max_length=4, label="expiration year")
    code = forms.CharField(max_length=4, label="security code")


class Purchase_option(forms.Form):
    search_key = forms.CharField()
    platform_key = forms.CharField()
    email = forms.EmailField()

    billing_first_name = forms.CharField()
    billing_middle_name = forms.CharField(required=False)
    billing_last_name = forms.CharField()
    billing_phone = forms.CharField()
    billing_address1 = forms.CharField()
    billing_address2 = forms.CharField(required=False)
    billing_city = forms.CharField()
    billing_province = forms.CharField()
    billing_postal_code = forms.CharField()
    billing_country = forms.CharField()

    card_number = forms.CharField(max_length=16, label="card number")
    card_month = forms.CharField(max_length=2, label="expiration month")
    card_year = forms.CharField(max_length=4, label="expiration year")
    card_code = forms.CharField(max_length=4, label="security code")


class DemoOptionForm(forms.Form):
    search_key = forms.CharField()
    platform_key = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)






class AddToStagingForm(forms.Form):
    flight_choice = forms.CharField(required=False)
    notes = forms.CharField(required=False)
    dep_date = forms.DateField()
    ret_date = forms.DateField()

    traveler_first_name = forms.CharField()
    traveler_middle_name = forms.CharField(required=False)
    traveler_last_name = forms.CharField()
    traveler_infant = forms.BooleanField(required=False, initial=False)
    traveler_gender = forms.CharField()
    traveler_birth_date = forms.DateField()
    traveler_passport_country = forms.CharField()
    traveler_seat_pref = forms.CharField(required=False)
    traveler_rewards_program = forms.CharField(required=False)
    traveler_contact_email = forms.EmailField(required=False)

class ExerStagingForm(forms.Form):
    fare = forms.FloatField()
    dep_date = forms.DateField()
    ret_date = forms.DateField()
    traveler_first_name = forms.CharField()
    traveler_middle_name = forms.CharField(required=False)
    traveler_last_name = forms.CharField()
    traveler_infant = forms.BooleanField(required=False, initial=False)
    traveler_gender = forms.CharField()
    traveler_birth_date = forms.DateField()
    traveler_passport_country = forms.CharField()
    traveler_seat_pref = forms.CharField(required=False)
    traveler_rewards_program = forms.CharField(required=False)
    traveler_contact_email = forms.EmailField(required=False)
    flight_purchased = forms.CharField(widget=forms.Textarea)
    notes = forms.CharField(required=False, widget=forms.Textarea)

class RefundStagingForm(forms.Form):
    notes = forms.CharField(required=False, widget=forms.Textarea)