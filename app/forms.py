from django import forms

class KeyForm(forms.Form):
    pass1= forms.CharField(label="New password", max_length=10)
    pass2= forms.CharField(label="Re-enter new password", max_length=10)

class cardname(forms.Form):
    holdername= forms.CharField(label="Card holder name", max_length=10)
