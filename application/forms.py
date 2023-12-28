from django import forms

class UserNameForm(forms.Form):
	StudentID = forms.CharField(max_length=30)