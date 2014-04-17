from django import forms

class PromoDetail(forms.Form):
    email = forms.EmailField()
    code = forms.CharField(label='Promo Code')
    platform_key = forms.CharField(label='Platform Key')
    
class ContestSubmissionForm(forms.Form):
    email = forms.EmailField()
    platform_key = forms.CharField(label='Platform Key')
    contest_key = forms.CharField(label='Contest Key')
    value = forms.FloatField(max_value=20000, min_value=0)

class CreatePromoForm(forms.Form):
    email = forms.EmailField()
    platform_key = forms.CharField(label='Platform Key')
    value = forms.FloatField(max_value=20000, min_value=0)
