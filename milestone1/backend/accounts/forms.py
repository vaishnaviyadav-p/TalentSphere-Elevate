from django import forms
from django.contrib.auth.models import User

ROLE_CHOICES = (
    ('candidate', 'Candidate'),
    ('recruiter', 'Recruiter'),
)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ROLE_CHOICES)